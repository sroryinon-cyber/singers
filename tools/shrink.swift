// shrink <in> <out.mp4> [videoBitrate]  – H.264 720p-class MP4 for the web, SDR, fast-start
import AVFoundation
import Foundation

let args = CommandLine.arguments
guard args.count >= 3 else { print("usage: shrink in out [bitrate]"); exit(2) }
let src = URL(fileURLWithPath: args[1]), dst = URL(fileURLWithPath: args[2])
let bitrate = args.count > 3 ? Int(args[3])! : 2_400_000
try? FileManager.default.removeItem(at: dst)

let asset = AVURLAsset(url: src)
guard let vtrack = asset.tracks(withMediaType: .video).first else { print("no video track"); exit(1) }
let atrack = asset.tracks(withMediaType: .audio).first

let comp = AVMutableVideoComposition(propertiesOf: asset)
comp.colorPrimaries = AVVideoColorPrimaries_ITU_R_709_2
comp.colorTransferFunction = AVVideoTransferFunction_ITU_R_709_2
comp.colorYCbCrMatrix = AVVideoYCbCrMatrix_ITU_R_709_2
if vtrack.nominalFrameRate > 31 { comp.frameDuration = CMTime(value: 1, timescale: 30) }
let rs = comp.renderSize
let scale = min(1, 1280 / max(rs.width, rs.height))
func even(_ x: CGFloat) -> Int { Int((x * scale / 2).rounded()) * 2 }
let w = even(rs.width), h = even(rs.height)

let reader = try AVAssetReader(asset: asset)
let vout = AVAssetReaderVideoCompositionOutput(
    videoTracks: [vtrack],
    videoSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange])
vout.videoComposition = comp
vout.alwaysCopiesSampleData = false
reader.add(vout)

var aout: AVAssetReaderTrackOutput?
if let a = atrack {
    let o = AVAssetReaderTrackOutput(track: a, outputSettings: [
        AVFormatIDKey: kAudioFormatLinearPCM, AVSampleRateKey: 44100, AVNumberOfChannelsKey: 2,
        AVLinearPCMBitDepthKey: 16, AVLinearPCMIsFloatKey: false,
        AVLinearPCMIsBigEndianKey: false, AVLinearPCMIsNonInterleaved: false])
    o.alwaysCopiesSampleData = false
    if reader.canAdd(o) { reader.add(o); aout = o }
}

let writer = try AVAssetWriter(outputURL: dst, fileType: .mp4)
writer.shouldOptimizeForNetworkUse = true
let vin = AVAssetWriterInput(mediaType: .video, outputSettings: [
    AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: w, AVVideoHeightKey: h,
    AVVideoCompressionPropertiesKey: [
        AVVideoAverageBitRateKey: bitrate,
        AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel,
        AVVideoMaxKeyFrameIntervalKey: 60,
        AVVideoExpectedSourceFrameRateKey: 30],
    AVVideoColorPropertiesKey: [
        AVVideoColorPrimariesKey: AVVideoColorPrimaries_ITU_R_709_2,
        AVVideoTransferFunctionKey: AVVideoTransferFunction_ITU_R_709_2,
        AVVideoYCbCrMatrixKey: AVVideoYCbCrMatrix_ITU_R_709_2]])
vin.expectsMediaDataInRealTime = false
writer.add(vin)
var ain: AVAssetWriterInput?
if aout != nil {
    let i = AVAssetWriterInput(mediaType: .audio, outputSettings: [
        AVFormatIDKey: kAudioFormatMPEG4AAC, AVSampleRateKey: 44100,
        AVNumberOfChannelsKey: 2, AVEncoderBitRateKey: 128_000])
    i.expectsMediaDataInRealTime = false
    writer.add(i); ain = i
}

guard reader.startReading() else { print("read error: \(String(describing: reader.error))"); exit(1) }
guard writer.startWriting() else { print("write error: \(String(describing: writer.error))"); exit(1) }
writer.startSession(atSourceTime: .zero)

let group = DispatchGroup()
let halve = vtrack.nominalFrameRate > 31   // 50/60fps source -> keep every other frame
func pump(_ input: AVAssetWriterInput, _ output: AVAssetReaderOutput, _ label: String) {
    group.enter()
    var index = 0
    input.requestMediaDataWhenReady(on: DispatchQueue(label: label)) {
        while input.isReadyForMoreMediaData {
            if let buf = output.copyNextSampleBuffer() {
                index += 1
                if halve && label == "video" && index % 2 == 0 { continue }
                if !input.append(buf) { reader.cancelReading(); input.markAsFinished(); group.leave(); return }
            } else { input.markAsFinished(); group.leave(); return }
        }
    }
}
pump(vin, vout, "video")
if let i = ain, let o = aout { pump(i, o, "audio") }
group.wait()

let done = DispatchSemaphore(value: 0)
writer.finishWriting { done.signal() }
done.wait()
if writer.status != .completed || reader.status == .failed {
    print("failed: writer=\(String(describing: writer.error)) reader=\(String(describing: reader.error))"); exit(1)
}
print("ok \(w)x\(h) -> \(dst.lastPathComponent)")
