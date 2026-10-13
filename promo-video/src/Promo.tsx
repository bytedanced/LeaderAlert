import React from "react";
import { Audio, Series, staticFile } from "remotion";
import { Scene1, Scene2, Scene3, Scene4, Scene5 } from "./scenes";

export const Promo: React.FC = () => {
  return (
    <>
      <Audio src={staticFile("narration.mp3")} />
      <Series>
        <Series.Sequence durationInFrames={140}>
          <Scene1 />
        </Series.Sequence>
        <Series.Sequence durationInFrames={120}>
          <Scene2 />
        </Series.Sequence>
        <Series.Sequence durationInFrames={100}>
          <Scene3 />
        </Series.Sequence>
        <Series.Sequence durationInFrames={100}>
          <Scene4 />
        </Series.Sequence>
        <Series.Sequence durationInFrames={80}>
          <Scene5 />
        </Series.Sequence>
      </Series>
    </>
  );
};
