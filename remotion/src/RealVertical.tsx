import React from "react";
import {AbsoluteFill, Audio, Img, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from "remotion";

type Asset = {title: string; image: string; start?: number; end?: number};
type Caption = {start: number; end: number; text: string};
type Props = {topic: string; title?: string; duration_seconds: number; fps: number; assets: Asset[]; audio: string; captions: Caption[]};

export const RealVertical: React.FC<Props> = ({assets, audio, captions}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const seconds = frame / fps;
  const currentCaption = captions.find((c) => seconds >= c.start && seconds < c.end)?.text ?? "";

  return (
    <AbsoluteFill style={{backgroundColor: "black", fontFamily: "Arial, sans-serif"}}>
      {assets.map((asset, index) => {
        const startSeconds = asset.start ?? (index * (durationInFrames / fps) / Math.max(assets.length, 1));
        const endSeconds = asset.end ?? ((index + 1) * (durationInFrames / fps) / Math.max(assets.length, 1));
        const start = Math.floor(startSeconds * fps);
        const end = Math.min(durationInFrames, Math.ceil(endSeconds * fps));
        const local = Math.max(0, frame - start);
        const sceneFrames = Math.max(1, end - start);
        const scale = interpolate(local, [0, sceneFrames], [1.06, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
        const opacity = interpolate(local, [0, 8, Math.max(8, sceneFrames - 8), sceneFrames], [0, 1, 1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
        return (
          <Sequence key={asset.image} from={start} durationInFrames={Math.max(1, end - start)}>
            <AbsoluteFill style={{opacity}}>
              <Img src={staticFile("assets/" + asset.image)} style={{width:"100%",height:"100%",objectFit:"cover",transform:"scale(" + scale + ")"}} />
              {asset.title && (
                <AbsoluteFill style={{justifyContent:"flex-start",padding:70}}>
                  <div style={{background:"rgba(0,0,0,.58)",borderRadius:24,padding:"18px 28px",alignSelf:"flex-start"}}>
                    <div style={{color:"white",fontSize:48,fontWeight:800}}>{asset.title}</div>
                  </div>
                </AbsoluteFill>
              )}
            </AbsoluteFill>
          </Sequence>
        );
      })}
      <Audio src={staticFile("assets/" + audio)} volume={1} />
      <AbsoluteFill style={{justifyContent:"flex-end",alignItems:"center",padding:55,paddingBottom:90,pointerEvents:"none"}}>
        {currentCaption && (
          <div style={{color:"white",fontSize:42,fontWeight:700,lineHeight:1.15,textAlign:"center",background:"rgba(0,0,0,.72)",borderRadius:24,padding:"18px 26px",maxWidth:930,textShadow:"0 2px 5px black"}}>
            {currentCaption}
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
