import Foundation
import Vision
import AppKit
let args=CommandLine.arguments
if args.count != 2 { fputs("image path required\n",stderr); exit(1) }
let url=URL(fileURLWithPath:args[1])
let request=VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "en-US"]
request.usesLanguageCorrection = true
request.minimumTextHeight = 0.015
let handler=VNImageRequestHandler(url:url,options:[:])
do {
 try handler.perform([request])
 let rows=(request.results ?? []).compactMap { r -> [String:Any]? in
  guard let c=r.topCandidates(1).first else{return nil}
  let b=r.boundingBox
  return ["text":c.string,"confidence":Double(c.confidence),"box":[Double(b.origin.x),Double(1-b.origin.y-b.height),Double(b.width),Double(b.height)]]
 }
 let result:[String:Any] = ["text":rows.compactMap{$0["text"] as? String}.joined(separator:"\n"),"lines":rows]
 let out=try JSONSerialization.data(withJSONObject:result)
 FileHandle.standardOutput.write(out)
} catch { fputs(error.localizedDescription,stderr);exit(2) }
