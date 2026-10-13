import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import {
  BossFigure,
  Burst,
  Caption,
  CowHead,
  DARK_BG,
  CREAM,
  INK,
  Keycap,
  Laptop,
  NotificationCard,
  Pill,
  PURPLE,
  RED,
  ScanFrame,
  StarIcon,
  Webcam,
  Worker,
  YELLOW,
  FONT,
} from "./cartoon";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// 通用：居中文字的绝对定位样式
const centerText = (top: number): React.CSSProperties => ({
  position: "absolute",
  top,
  left: 0,
  right: 0,
  textAlign: "center",
  fontFamily: FONT,
});

// ============ 场景 1：摸鱼被逮（0-140） ============
export const Scene1: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = (delay: number, damping = 12) =>
    spring({ frame: frame - delay, fps, config: { damping, stiffness: 180, mass: 0.7 } });

  const titleIn = pop(3);
  const workerIn = pop(10);
  const laptopIn = pop(14);
  const bossIn = spring({ frame: frame - 48, fps, config: { damping: 15, stiffness: 110, mass: 1 } });
  const burstIn = pop(62, 9);
  const capIn = pop(74);
  const panic = frame >= 62;

  // 老板落地后的屏幕抖动（62-82 帧）
  const st = frame - 62;
  const shake = st >= 0 && st <= 20 ? Math.sin(st * 1.6) * 12 * (1 - st / 20) : 0;

  return (
    <AbsoluteFill style={{ background: CREAM }}>
      {/* 老板驾到时的压暗 */}
      <AbsoluteFill style={{ background: "#000", opacity: bossIn * 0.1 }} />
      <div style={{ width: "100%", height: "100%", transform: `translateX(${shake}px)`, position: "relative" }}>
        {/* 标题 */}
        <div
          style={{
            ...centerText(250),
            fontSize: 108,
            fontWeight: 900,
            color: INK,
            letterSpacing: 4,
            transform: `scale(${titleIn}) rotate(-3deg)`,
            opacity: titleIn,
          }}
        >
          摸鱼最怕什么？
        </div>

        {/* 地面阴影 */}
        <div
          style={{
            position: "absolute",
            left: 200,
            top: 1465,
            width: 680,
            height: 60,
            borderRadius: "50%",
            background: "rgba(43,43,58,0.12)",
          }}
        />

        {/* 打工人 */}
        <div
          style={{
            position: "absolute",
            left: 190,
            top: 790,
            transform: `translateY(${(1 - workerIn) * 400}px) scale(${workerIn})`,
            opacity: workerIn,
          }}
        >
          <Worker size={330} panic={panic} />
        </div>

        {/* 笔记本（视频页） */}
        <div
          style={{
            position: "absolute",
            left: 230,
            top: 1130,
            transform: `translateY(${(1 - laptopIn) * 400}px) scale(${laptopIn})`,
            opacity: laptopIn,
          }}
        >
          <Laptop size={620} screen="video" />
        </div>

        {/* 老板剪影从右侧滑入 */}
        <div
          style={{
            position: "absolute",
            left: 640,
            top: 760,
            transform: `translateX(${(1 - bossIn) * 620}px)`,
            opacity: bossIn,
          }}
        >
          <BossFigure size={430} />
        </div>

        {/* 感叹号爆炸贴 */}
        <div
          style={{
            position: "absolute",
            left: 545,
            top: 620,
            transform: `scale(${burstIn}) rotate(12deg)`,
            opacity: burstIn,
          }}
        >
          <Burst size={180} />
        </div>

        {/* 字幕 */}
        <div
          style={{
            position: "absolute",
            top: 1650,
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            transform: `scale(${capIn})`,
            opacity: capIn,
          }}
        >
          <Caption text="上一秒刷视频，下一秒站身后" />
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ============ 场景 2：识别 + 全网广播（140-260） ============
export const Scene2: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = (delay: number, damping = 12) =>
    spring({ frame: frame - delay, fps, config: { damping, stiffness: 180, mass: 0.7 } });

  const camIn = pop(2);
  const faceIn = pop(8);
  const chipIn = pop(40);
  const capIn = pop(62);

  const scanY = interpolate(frame % 36, [0, 36], [0, 300]);
  const beamOpacity = 0.1 + 0.06 * Math.sin(frame * 0.2);

  const laptopXs = [60, 410, 760];

  return (
    <AbsoluteFill style={{ background: DARK_BG }}>
      {/* 摄像头 */}
      <div
        style={{
          position: "absolute",
          left: 460,
          top: 190,
          transform: `scale(${camIn})`,
          opacity: camIn,
        }}
      >
        <Webcam size={160} />
      </div>

      {/* 扫描光束 */}
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <polygon points="540,360 350,920 730,920" fill={YELLOW} opacity={beamOpacity} />
      </svg>

      {/* 被识别的老板脸 + 扫描框 */}
      <div
        style={{
          position: "absolute",
          left: 390,
          top: 620,
          transform: `scale(${faceIn})`,
          opacity: faceIn,
        }}
      >
        <BossFigure size={300} />
      </div>
      <div style={{ position: "absolute", left: 370, top: 590, opacity: faceIn }}>
        <ScanFrame size={340} />
      </div>
      {/* 扫描线 */}
      <div
        style={{
          position: "absolute",
          left: 380,
          top: 600 + scanY,
          width: 320,
          height: 8,
          borderRadius: 4,
          background: YELLOW,
          opacity: frame >= 10 && frame <= 46 ? 0.85 : 0,
          boxShadow: `0 0 24px ${YELLOW}`,
        }}
      />

      {/* 识别成功 chip */}
      <div
        style={{
          position: "absolute",
          top: 1010,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          transform: `scale(${chipIn})`,
          opacity: chipIn,
        }}
      >
        <Pill text="识别成功：张总" fontSize={48} />
      </div>

      {/* 广播波纹 */}
      {[0, 10, 20].map((d) => {
        const t = interpolate(frame - 55 - d, [0, 32], [0, 1], clamp);
        const r = t * 500;
        return (
          <div
            key={d}
            style={{
              position: "absolute",
              left: 540 - r,
              top: 1160 - r,
              width: r * 2,
              height: r * 2,
              borderRadius: "50%",
              border: `6px solid ${YELLOW}`,
              opacity: t <= 0 ? 0 : (1 - t) * 0.7,
            }}
          />
        );
      })}

      {/* 三台电脑 + 迷你通知 */}
      {laptopXs.map((x, i) => {
        const lapIn = pop(58 + i * 8);
        const cardIn = pop(74 + i * 8);
        return (
          <React.Fragment key={i}>
            <div
              style={{
                position: "absolute",
                left: x,
                top: 1440,
                transform: `translateY(${(1 - lapIn) * 160}px) scale(${0.5 + lapIn * 0.5})`,
                opacity: lapIn,
              }}
            >
              <Laptop size={260} screen="code" />
            </div>
            <div
              style={{
                position: "absolute",
                left: x - 40,
                top: 1275,
                transform: `scale(${cardIn}) rotate(${i === 1 ? 0 : i === 0 ? -4 : 4}deg)`,
                opacity: cardIn,
              }}
            >
              <NotificationCard width={330} title="预警" big="牛来了！" dark />
            </div>
          </React.Fragment>
        );
      })}

      {/* 字幕 */}
      <div
        style={{
          position: "absolute",
          top: 1770,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          transform: `scale(${capIn})`,
          opacity: capIn,
        }}
      >
        <Caption text="摄像头认出 TA，立刻全网广播" dark fontSize={50} />
      </div>
    </AbsoluteFill>
  );
};

// ============ 场景 3：Alt+Tab 秒切（260-360） ============
export const Scene3: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = (delay: number, damping = 12) =>
    spring({ frame: frame - delay, fps, config: { damping, stiffness: 180, mass: 0.7 } });

  const cardIn = pop(2, 10);
  const lapIn = pop(8);
  const keyIn1 = pop(40);
  const keyIn2 = pop(46);
  const capIn = pop(52);

  // 翻屏：18-26 收起，26 换内容，26-34 展开
  const flip =
    frame < 26
      ? interpolate(frame, [18, 26], [1, 0], clamp)
      : interpolate(frame, [26, 34], [0, 1], clamp);
  const screen = frame < 26 ? "video" : "code";
  const pressed = frame >= 56 && frame <= 63;
  const speedOpacity = frame >= 18 && frame <= 34 ? 0.8 : 0;

  return (
    <AbsoluteFill style={{ background: CREAM }}>
      {/* 通知卡片 */}
      <div
        style={{
          position: "absolute",
          left: 280,
          top: 170,
          transform: `scale(${cardIn}) rotate(-3deg)`,
          opacity: cardIn,
        }}
      >
        <NotificationCard width={540} />
      </div>

      {/* 翻屏速度线 */}
      {[300, 420, 980].map((y, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: i === 2 ? 60 : 940,
            top: y + 380,
            width: 110,
            height: 12,
            borderRadius: 6,
            background: INK,
            opacity: speedOpacity,
            transform: `rotate(${i === 2 ? 20 : -20}deg)`,
          }}
        />
      ))}

      {/* 大笔记本 */}
      <div
        style={{
          position: "absolute",
          left: 140,
          top: 640,
          transform: `scale(${lapIn}) scaleX(${Math.max(flip, 0.001) * lapIn})`,
          opacity: lapIn,
        }}
      >
        <Laptop size={800} screen={screen as "video" | "code"} />
      </div>

      {/* Alt + Tab 键帽 */}
      <div
        style={{
          position: "absolute",
          top: 1290,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: 36,
        }}
      >
        <div style={{ transform: `scale(${keyIn1})`, opacity: keyIn1 }}>
          <Keycap label="Alt" size={120} pressed={pressed} />
        </div>
        <div
          style={{
            fontSize: 72,
            fontWeight: 900,
            color: INK,
            fontFamily: FONT,
            transform: `scale(${keyIn1})`,
            opacity: keyIn1,
          }}
        >
          +
        </div>
        <div style={{ transform: `scale(${keyIn2})`, opacity: keyIn2 }}>
          <Keycap label="Tab" size={120} pressed={pressed} />
        </div>
      </div>

      {/* 字幕 */}
      <div
        style={{
          position: "absolute",
          top: 1580,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          transform: `scale(${capIn})`,
          opacity: capIn,
        }}
      >
        <Caption text="Alt + Tab，一秒切回战斗状态" />
      </div>
    </AbsoluteFill>
  );
};

// ============ 场景 4：产品亮相（360-460） ============
export const Scene4: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = (delay: number, damping = 12) =>
    spring({ frame: frame - delay, fps, config: { damping, stiffness: 180, mass: 0.7 } });

  const cowIn = spring({ frame: frame - 4, fps, config: { damping: 8, stiffness: 160, mass: 0.8 } });
  const titleIn = pop(16);
  const subIn = pop(22);
  const noteIn = pop(56);

  const pills = ["无服务器", "本地识别", "多目标预警", "开源免费"];
  const sparkles = [
    { x: 150, y: 320, s: 46 },
    { x: 880, y: 260, s: 60 },
    { x: 920, y: 700, s: 44 },
    { x: 110, y: 760, s: 52 },
    { x: 820, y: 980, s: 40 },
  ];

  return (
    <AbsoluteFill
      style={{ background: `linear-gradient(160deg, ${PURPLE} 0%, #4C1D95 100%)` }}
    >
      {/* 闪烁星星 */}
      {sparkles.map((sp, i) => {
        const tw = 0.55 + 0.45 * Math.sin(frame * 0.15 + i * 1.3);
        return (
          <div key={i} style={{ position: "absolute", left: sp.x, top: sp.y, opacity: tw, transform: `scale(${tw})` }}>
            <StarIcon size={sp.s} />
          </div>
        );
      })}

      {/* 牛头 logo */}
      <div
        style={{
          position: "absolute",
          left: 330,
          top: 290,
          transform: `scale(${cowIn}) rotate(${(1 - cowIn) * -30}deg)`,
          opacity: cowIn,
        }}
      >
        <CowHead size={420} />
      </div>

      {/* 标题 */}
      <div
        style={{
          ...centerText(810),
          fontSize: 150,
          fontWeight: 900,
          color: "#fff",
          letterSpacing: 10,
          textShadow: `7px 7px 0 rgba(43,43,58,0.6)`,
          transform: `translateY(${(1 - titleIn) * 90}px)`,
          opacity: titleIn,
        }}
      >
        牛来了预警
      </div>
      <div
        style={{
          ...centerText(1000),
          fontSize: 60,
          fontWeight: 700,
          color: "#DDD6FE",
          letterSpacing: 8,
          transform: `translateY(${(1 - subIn) * 60}px)`,
          opacity: subIn,
        }}
      >
        LeaderAlert
      </div>

      {/* 特性药丸 */}
      {[0, 1].map((row) => (
        <div
          key={row}
          style={{
            position: "absolute",
            top: 1160 + row * 130,
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            gap: 40,
          }}
        >
          {pills.slice(row * 2, row * 2 + 2).map((p, i) => {
            const pillIn = pop(30 + (row * 2 + i) * 6);
            return (
              <div key={p} style={{ transform: `scale(${pillIn})`, opacity: pillIn }}>
                <Pill text={p} fontSize={46} />
              </div>
            );
          })}
        </div>
      ))}

      {/* 底部一句话 */}
      <div
        style={{
          ...centerText(1700),
          fontSize: 48,
          fontWeight: 700,
          color: "rgba(255,255,255,0.75)",
          letterSpacing: 4,
          opacity: noteIn,
        }}
      >
        一个摄像头，全组人保命
      </div>
    </AbsoluteFill>
  );
};

// ============ 场景 5：CTA 点 Star（460-540） ============
export const Scene5: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = (delay: number, damping = 12) =>
    spring({ frame: frame - delay, fps, config: { damping, stiffness: 180, mass: 0.7 } });

  const cowIn = pop(2);
  const line1In = pop(6);
  const starOutlineIn = pop(14);
  const starFillIn = spring({ frame: frame - 30, fps, config: { damping: 8, stiffness: 200, mass: 0.6 } });
  const ctaIn = pop(40);
  const repoIn = pop(48);
  const mitIn = pop(54);

  return (
    <AbsoluteFill style={{ background: "#0F0A1E" }}>
      {/* 小牛头 */}
      <div
        style={{
          position: "absolute",
          left: 465,
          top: 220,
          transform: `scale(${cowIn})`,
          opacity: cowIn,
        }}
      >
        <CowHead size={150} />
      </div>

      <div
        style={{
          ...centerText(430),
          fontSize: 82,
          fontWeight: 900,
          color: "#fff",
          letterSpacing: 4,
          transform: `translateY(${(1 - line1In) * 60}px)`,
          opacity: line1In,
        }}
      >
        GitHub 搜 <span style={{ color: "#C4B5FD" }}>LeaderAlert</span>
      </div>

      {/* 星星：先描边，后填充 */}
      <div
        style={{
          position: "absolute",
          left: 400,
          top: 660,
          transform: `scale(${starOutlineIn})`,
          opacity: starOutlineIn,
        }}
      >
        <StarIcon size={280} filled={false} />
      </div>
      <div
        style={{
          position: "absolute",
          left: 400,
          top: 660,
          transform: `scale(${starFillIn})`,
          opacity: starFillIn,
        }}
      >
        <StarIcon size={280} filled />
      </div>

      {/* 星星爆发光线 */}
      {starFillIn > 0.2 &&
        [0, 45, 90, 135, 180, 225, 270, 315].map((deg) => {
          const t = interpolate(frame - 30, [0, 14], [0, 1], clamp);
          return (
            <div
              key={deg}
              style={{
                position: "absolute",
                left: 540,
                top: 800,
                width: 10,
                height: 70,
                borderRadius: 5,
                background: YELLOW,
                opacity: (1 - t) * 0.9,
                transform: `rotate(${deg}deg) translateY(${-170 - t * 110}px)`,
                transformOrigin: "0 0",
              }}
            />
          );
        })}

      {/* CTA */}
      <div
        style={{
          ...centerText(1130),
          fontSize: 108,
          fontWeight: 900,
          color: YELLOW,
          letterSpacing: 6,
          textShadow: `6px 6px 0 rgba(43,43,58,0.9)`,
          transform: `scale(${ctaIn}) rotate(-2deg)`,
          opacity: ctaIn,
        }}
      >
        点个 Star 防身
      </div>

      <div
        style={{
          ...centerText(1330),
          fontSize: 40,
          fontWeight: 600,
          color: "#94A3B8",
          letterSpacing: 2,
          opacity: repoIn,
        }}
      >
        github.com/bytedanced/LeaderAlert
      </div>

      <div
        style={{
          ...centerText(1760),
          fontSize: 38,
          fontWeight: 600,
          color: "#64748B",
          letterSpacing: 2,
          opacity: mitIn,
        }}
      >
        MIT 开源 · 仅供学习交流，摸鱼后果自负
      </div>
    </AbsoluteFill>
  );
};
