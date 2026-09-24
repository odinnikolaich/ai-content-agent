import React from "react";
import {Composition, registerRoot} from "remotion";
import {RealVertical} from "./RealVertical";

type Props = {
  assets: Array<{title: string; image: string; start?: number; end?: number}>;
  audio: string;
  captions: Array<{start: number; end: number; text: string}>;
  duration_seconds: number;
  fps: number;
  topic: string;
  title?: string;
};

export const RemotionRoot: React.FC = () => (
  <Composition
    id="RealVertical"
    component={RealVertical}
    durationInFrames={50 * 30}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={{assets: [], audio: "voice_ru.mp3", captions: [], duration_seconds: 50, fps: 30, topic: "", title: ""}}
    calculateMetadata={({props}) => ({
      durationInFrames: Math.round(props.duration_seconds * props.fps),
      fps: props.fps,
      width: 1080,
      height: 1920,
    })}
  />
);

registerRoot(RemotionRoot);
