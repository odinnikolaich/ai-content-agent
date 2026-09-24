import React from "react";
import {AbsoluteFill, Audio, Img, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from "remotion";

type Asset = {title: string; image: string};
type Props = {topic: string; duration_seconds: number; assets: Asset[]; audio: string; narration: string};

export const RealVertical: React.FC<Props> = ({assets, audio, narration}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const perScene = Math.floor(durationInFrames / Math.max(assets.length, 1));

  return (
    <AbsoluteFill style={{backgroundColor: "black", fontFamily: "Arial, sans-serif"}}>
      {assets.map((asset, index) => {
        const start = index * perScene;
        const end = index === assets.length - 1 ? durationInFrames : (index + 1) * perScene;
        const local = frame - start;
        const scale = interpolate(local, [0, perScene], [1.06, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
        const opacity = interpolate(local, [0, 8, perScene - 8, perScene], [0, 1, 1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
        return (
          <Sequence key={asset.image} from={start} durationInFrames={end - start}>
            <AbsoluteFill style={{opacity}}>
              <Img src={staticFile("assets/real-demo/" + asset.image)} style={{width:"100%",height:"100%",objectFit:"cover",transform:"scale("+scale+")"}} />
              <AbsoluteFill style={{justifyContent:"flex-end",padding:70,paddingBottom:210}}>
                <div style={{background:"rgba(0,0,0,.62)",borderRadius:28,padding:"22px 30px",alignSelf:"flex-start",maxWidth:900}}>
                  <div style={{color:"white",fontSize:64,fontWeight:800,lineHeight:1.05}}>{asset.title}</div>
                </div>
              </AbsoluteFill>
            </AbsoluteFill>
          </Sequence>
        );
      })}
      <Audio src={staticFile("assets/real-demo/" + audio)} volume={1} />
      <AbsoluteFill style={{justifyContent:"flex-end",alignItems:"center",paddingBottom:65,pointerEvents:"none"}}>
        <div style={{color:"white",fontSize:31,textAlign:"center",textShadow:"0 2px 8px black",maxWidth:920}}>
          {narration.slice(0, Math.max(1, Math.floor((frame / fps) * 22)))}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
