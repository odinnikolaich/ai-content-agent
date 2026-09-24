import React from "react";
import {AbsoluteFill, Audio, Img, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from "remotion";

type Asset = {title: string; image: string};
type Caption = {start: number; end: number; text: string};
type Props = {topic: string; duration_seconds: number; assets: Asset[]; audio: string; captions: Caption[]};

export const RealVertical: React.FC<Props> = ({assets, audio, captions}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const perScene = Math.floor(durationInFrames / Math.max(assets.length, 1));
  const seconds = frame / fps;
  const currentCaption = captions.find((c) => seconds >= c.start && seconds < c.end)?.text ?? "";

  return (
    <AbsoluteFill style={{backgroundColor: "black", fontFamily: "Arial, sans-serif"}}>
      {assets.map((asset, index) => {
        const start = index * perScene;
        const end = index === assets.length - 1 ? durationInFrames : (index + 1) * perScene;
        const local = frame - start;
        const scale = interpolate(local, [0, perScene], [1.06, 1], {extrapolateLeft:"clamp", extrapolateRight:"clamp"});
        const opacity = interpolate(local, [0, 8, perScene - 8, perScene], [0, 1, 1, 0], {extrapolateLeft:"clamp", extrapolateRight:"clamp"});
        return (
          <Sequence key={asset.image} from={start} durationInFrames={end-start}>
            <AbsoluteFill style={{opacity}}>
              <Img src={staticFile("assets/real-demo/" + asset.image)}
                style={{width:"100%",height:"100%",objectFit:"cover",transform:"scale("+scale+")"}} />
              <AbsoluteFill style={{justifyContent:"flex-start",padding:70}}>
                <div style={{background:"rgba(0,0,0,.58)",borderRadius:24,padding:"18px 28px",alignSelf:"flex-start"}}>
                  <div style={{color:"white",fontSize:58,fontWeight:800}}>{asset.title}</div>
                </div>
              </AbsoluteFill>
            </AbsoluteFill>
          </Sequence>
        );
      })}
      <Audio src={staticFile("assets/real-demo/" + audio)} volume={1} />
      <AbsoluteFill style={{justifyContent:"flex-end",alignItems:"center",padding:55,paddingBottom:90,pointerEvents:"none"}}>
        {currentCaption && (
          <div style={{
            color:"white",fontSize:42,fontWeight:700,lineHeight:1.15,textAlign:"center",
            background:"rgba(0,0,0,.72)",borderRadius:24,padding:"18px 26px",maxWidth:930,
            textShadow:"0 2px 5px black"
          }}>{currentCaption}</div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
