import React from "react";
import {Composition, registerRoot} from "remotion";
import {RealVertical} from "./RealVertical";

export const RemotionRoot: React.FC = () => (
  <Composition
    id="RealVertical"
    component={RealVertical}
    durationInFrames={43 * 30}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={{assets: [], audio: "voice_ru.mp3", duration_seconds: 43, topic: "", narration: ""}}
  />
);

registerRoot(RemotionRoot);
