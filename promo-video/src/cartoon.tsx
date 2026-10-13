import React from "react";

// 色板
export const INK = "#2B2B3A";
export const CREAM = "#FFF6E9";
export const PURPLE = "#7C3AED";
export const PURPLE_DARK = "#5B21B6";
export const RED = "#F87171";
export const YELLOW = "#FBBF24";
export const PINK = "#F9A8D4";
export const SKY = "#7DD3FC";
export const DARK_BG = "#151022";
export const FONT = '"Microsoft YaHei", "PingFang SC", sans-serif';

// ============ 牛头 logo ============
export const CowHead: React.FC<{ size?: number }> = ({ size = 200 }) => (
  <svg width={size} height={size} viewBox="0 0 200 200">
    {/* 牛角 */}
    <path
      d="M58 46 Q46 12 74 20 Q64 34 70 48 Z"
      fill={YELLOW}
      stroke={INK}
      strokeWidth={6}
      strokeLinejoin="round"
    />
    <path
      d="M142 46 Q154 12 126 20 Q136 34 130 48 Z"
      fill={YELLOW}
      stroke={INK}
      strokeWidth={6}
      strokeLinejoin="round"
    />
    {/* 耳朵 */}
    <ellipse
      cx={30}
      cy={96}
      rx={22}
      ry={14}
      fill="#fff"
      stroke={INK}
      strokeWidth={6}
      transform="rotate(-25 30 96)"
    />
    <ellipse
      cx={170}
      cy={96}
      rx={22}
      ry={14}
      fill="#fff"
      stroke={INK}
      strokeWidth={6}
      transform="rotate(25 170 96)"
    />
    {/* 头 */}
    <ellipse cx={100} cy={110} rx={72} ry={66} fill="#fff" stroke={INK} strokeWidth={7} />
    {/* 黑色斑块 */}
    <path d="M50 78 Q64 56 88 66 Q84 92 56 94 Z" fill={INK} opacity={0.85} />
    {/* 眼睛 */}
    <circle cx={79} cy={102} r={8} fill={INK} />
    <circle cx={124} cy={102} r={8} fill={INK} />
    <circle cx={82} cy={99} r={2.6} fill="#fff" />
    <circle cx={127} cy={99} r={2.6} fill="#fff" />
    {/* 腮红 */}
    <circle cx={58} cy={124} r={8} fill={PINK} opacity={0.6} />
    <circle cx={144} cy={124} r={8} fill={PINK} opacity={0.6} />
    {/* 鼻 */}
    <ellipse cx={101} cy={148} rx={44} ry={28} fill={PINK} stroke={INK} strokeWidth={6} />
    <ellipse cx={87} cy={148} rx={5.5} ry={8.5} fill={INK} />
    <ellipse cx={115} cy={148} rx={5.5} ry={8.5} fill={INK} />
  </svg>
);

// ============ 打工人 ============
export const Worker: React.FC<{ size?: number; panic?: boolean }> = ({
  size = 240,
  panic = false,
}) => (
  <svg width={size} height={size} viewBox="0 0 200 200">
    {/* 身体 */}
    <path
      d="M46 200 Q46 138 100 138 Q154 138 154 200 Z"
      fill={PURPLE}
      stroke={INK}
      strokeWidth={6}
    />
    {/* 头 */}
    <circle cx={100} cy={94} r={48} fill="#FFDFC4" stroke={INK} strokeWidth={6} />
    {/* 头发 */}
    <path
      d="M52 88 Q55 42 100 42 Q145 42 148 88 Q130 62 118 70 Q108 52 92 66 Q70 60 52 88 Z"
      fill={INK}
    />
    {panic ? (
      <>
        <circle cx={83} cy={98} r={6} fill={INK} />
        <circle cx={117} cy={98} r={6} fill={INK} />
        <ellipse cx={100} cy={122} rx={8} ry={10} fill={INK} />
        {/* 汗滴 */}
        <path
          d="M150 68 q11 17 0 26 q-11 -9 0 -26"
          fill={SKY}
          stroke={INK}
          strokeWidth={4}
          strokeLinejoin="round"
        />
        <path
          d="M50 62 q-11 17 0 26 q11 -9 0 -26"
          fill={SKY}
          stroke={INK}
          strokeWidth={4}
          strokeLinejoin="round"
        />
      </>
    ) : (
      <>
        <path d="M74 96 Q82 90 90 96" stroke={INK} strokeWidth={5} fill="none" strokeLinecap="round" />
        <path d="M110 96 Q118 90 126 96" stroke={INK} strokeWidth={5} fill="none" strokeLinecap="round" />
        <path d="M88 118 Q100 128 112 118" stroke={INK} strokeWidth={5} fill="none" strokeLinecap="round" />
      </>
    )}
  </svg>
);

// ============ 老板剪影 ============
export const BossFigure: React.FC<{ size?: number }> = ({ size = 280 }) => (
  <svg width={size} height={size * 1.1} viewBox="0 0 200 220">
    <path d="M28 220 Q28 128 100 128 Q172 128 172 220 Z" fill={INK} />
    <circle cx={100} cy={86} r={52} fill={INK} />
    {/* 领带 */}
    <path d="M100 136 l-11 18 l11 48 l11 -48 Z" fill={RED} stroke={INK} strokeWidth={4} strokeLinejoin="round" />
    {/* 红眼 + 怒眉 */}
    <circle cx={82} cy={84} r={6} fill={RED} />
    <circle cx={118} cy={84} r={6} fill={RED} />
    <path d="M68 68 l22 9 M132 68 l-22 9" stroke={RED} strokeWidth={5} strokeLinecap="round" />
  </svg>
);

// ============ 笔记本电脑 ============
const CODE_ROWS: Array<Array<{ x: number; w: number; c: string }>> = [
  [
    { x: 40, w: 34, c: PURPLE },
    { x: 80, w: 60, c: SKY },
    { x: 146, w: 40, c: "#4ADE80" },
  ],
  [
    { x: 56, w: 46, c: "#4ADE80" },
    { x: 108, w: 74, c: "#94A3B8" },
  ],
  [
    { x: 56, w: 30, c: YELLOW },
    { x: 92, w: 88, c: SKY },
    { x: 186, w: 34, c: "#94A3B8" },
  ],
  [
    { x: 72, w: 62, c: "#94A3B8" },
    { x: 140, w: 44, c: RED },
  ],
  [
    { x: 40, w: 50, c: PURPLE },
    { x: 96, w: 36, c: "#4ADE80" },
  ],
];

export const Laptop: React.FC<{
  size?: number;
  screen: "video" | "code" | "blank";
}> = ({ size = 320, screen }) => (
  <svg width={size} height={size * 0.66} viewBox="0 0 320 212">
    {/* 屏幕 */}
    <rect x={20} y={6} width={280} height={170} rx={14} fill="#1E293B" stroke={INK} strokeWidth={7} />
    {screen === "video" && (
      <>
        <rect x={36} y={22} width={248} height={104} rx={8} fill="#0F172A" />
        <path d="M138 52 l46 26 l-46 26 Z" fill="#fff" opacity={0.92} />
        <rect x={36} y={136} width={248} height={8} rx={4} fill="#334155" />
        <rect x={36} y={136} width={142} height={8} rx={4} fill={RED} />
        <circle cx={178} cy={140} r={7} fill="#fff" />
        <rect x={36} y={152} width={120} height={8} rx={4} fill="#475569" />
      </>
    )}
    {screen === "code" &&
      CODE_ROWS.map((row, i) =>
        row.map((seg, j) => (
          <rect
            key={`${i}-${j}`}
            x={seg.x}
            y={28 + i * 26}
            width={seg.w}
            height={12}
            rx={6}
            fill={seg.c}
            opacity={0.9}
          />
        ))
      )}
    {/* 底座 */}
    <path
      d="M6 184 h308 l14 16 q3 6 -6 6 h-324 q-9 0 -6 -6 Z"
      fill="#CBD5E1"
      stroke={INK}
      strokeWidth={6}
      strokeLinejoin="round"
    />
    <rect x={128} y={188} width={64} height={6} rx={3} fill="#94A3B8" />
  </svg>
);

// ============ 摄像头 ============
export const Webcam: React.FC<{ size?: number }> = ({ size = 160 }) => (
  <svg width={size} height={size} viewBox="0 0 160 160">
    <circle cx={80} cy={66} r={46} fill="#fff" stroke={INK} strokeWidth={7} />
    <circle cx={80} cy={66} r={26} fill={INK} />
    <circle cx={88} cy={58} r={8} fill={SKY} />
    <circle cx={118} cy={38} r={7} fill={RED} />
    <path d="M62 112 h36 l6 22 h-48 Z" fill="#fff" stroke={INK} strokeWidth={6} strokeLinejoin="round" />
    <rect x={44} y={134} width={72} height={12} rx={6} fill="#fff" stroke={INK} strokeWidth={6} />
  </svg>
);

// ============ 识别扫描框 ============
export const ScanFrame: React.FC<{ size?: number; color?: string }> = ({
  size = 300,
  color = YELLOW,
}) => {
  const l = size * 0.22;
  const w = 9;
  const corners: Array<{ x: number; y: number; rot: number }> = [
    { x: 0, y: 0, rot: 0 },
    { x: size, y: 0, rot: 90 },
    { x: size, y: size, rot: 180 },
    { x: 0, y: size, rot: 270 },
  ];
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {corners.map((c, i) => (
        <path
          key={i}
          d={`M0 ${l} V${w} Q0 0 ${w} 0 H${l}`}
          fill="none"
          stroke={color}
          strokeWidth={w}
          strokeLinecap="round"
          transform={`rotate(${c.rot} ${c.x} ${c.y}) translate(${c.x} ${c.y})`}
        />
      ))}
    </svg>
  );
};

// ============ 红色感叹号爆炸贴 ============
const burstPath = (cx: number, cy: number, r1: number, r2: number, points: number): string => {
  let d = "";
  for (let i = 0; i < points * 2; i++) {
    const r = i % 2 === 0 ? r1 : r2;
    const a = (Math.PI * i) / points - Math.PI / 2;
    const x = cx + Math.cos(a) * r;
    const y = cy + Math.sin(a) * r;
    d += `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)} `;
  }
  return d + "Z";
};

export const Burst: React.FC<{ size?: number }> = ({ size = 150 }) => (
  <svg width={size} height={size} viewBox="0 0 150 150">
    <path
      d={burstPath(75, 75, 68, 50, 12)}
      fill={RED}
      stroke={INK}
      strokeWidth={5}
      strokeLinejoin="round"
    />
    <text
      x={75}
      y={98}
      textAnchor="middle"
      fontSize={76}
      fontWeight={900}
      fill="#fff"
      fontFamily="Arial Black, Arial"
    >
      !
    </text>
  </svg>
);

// ============ 星星 ============
export const StarIcon: React.FC<{ size?: number; filled?: boolean; color?: string }> = ({
  size = 100,
  filled = true,
  color = YELLOW,
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24">
    <path
      d="M12 2.2 l2.95 6.2 6.75 1.05 -4.85 4.55 1.1 6.7 -5.95 -3.1 -5.95 3.1 1.1 -6.7 -4.85 -4.55 6.75 -1.05 Z"
      fill={filled ? color : "none"}
      stroke={INK}
      strokeWidth={1.5}
      strokeLinejoin="round"
    />
  </svg>
);

// ============ 键帽（HTML） ============
export const Keycap: React.FC<{ label: string; size?: number; pressed?: boolean }> = ({
  label,
  size = 92,
  pressed = false,
}) => (
  <div
    style={{
      width: size,
      height: size,
      borderRadius: 18,
      background: "#fff",
      border: `5px solid ${INK}`,
      boxShadow: pressed ? `0 2px 0 ${INK}` : `0 9px 0 ${INK}`,
      transform: pressed ? "translateY(7px)" : "none",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontFamily: FONT,
      fontWeight: 800,
      fontSize: size * 0.36,
      color: INK,
    }}
  >
    {label}
  </div>
);

// ============ 通知卡片（HTML） ============
export const NotificationCard: React.FC<{
  width?: number;
  title?: string;
  big?: string;
  dark?: boolean;
  compact?: boolean;
}> = ({ width = 460, title = "牛来了预警", big = "牛来了：张总", dark = false, compact = false }) => {
  const iconSize = compact ? 64 : 96;
  const titleSize = compact ? 24 : 30;
  const bigSize = compact ? 38 : 52;
  return (
    <div
      style={{
        width,
        borderRadius: compact ? 18 : 24,
        background: dark ? "#241D3A" : "#fff",
        border: `5px solid ${INK}`,
        boxShadow: `8px 8px 0 rgba(43,43,58,0.9)`,
        padding: compact ? "14px 18px" : "22px 26px",
        display: "flex",
        alignItems: "center",
        gap: compact ? 14 : 20,
        fontFamily: FONT,
      }}
    >
      <div style={{ flexShrink: 0 }}>
        <CowHead size={iconSize} />
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <div
          style={{
            fontSize: titleSize,
            fontWeight: 700,
            color: dark ? "#B7A8E8" : "#8B8B9E",
            letterSpacing: 2,
          }}
        >
          {title}
        </div>
        <div style={{ fontSize: bigSize, fontWeight: 900, color: dark ? "#fff" : INK, whiteSpace: "nowrap" }}>
          {big}
        </div>
      </div>
    </div>
  );
};

// ============ 底部字幕条（HTML） ============
export const Caption: React.FC<{ text: string; dark?: boolean; fontSize?: number }> = ({
  text,
  dark = false,
  fontSize = 54,
}) => (
  <div
    style={{
      fontFamily: FONT,
      fontSize,
      fontWeight: 800,
      color: dark ? "#fff" : INK,
      background: dark ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.75)",
      border: `4px solid ${dark ? "rgba(255,255,255,0.25)" : INK}`,
      borderRadius: 999,
      padding: "16px 48px",
      whiteSpace: "nowrap",
    }}
  >
    {text}
  </div>
);

// ============ 特性药丸（HTML） ============
export const Pill: React.FC<{ text: string; fontSize?: number }> = ({ text, fontSize = 44 }) => (
  <div
    style={{
      fontFamily: FONT,
      fontSize,
      fontWeight: 800,
      color: PURPLE_DARK,
      background: "#fff",
      border: `4px solid ${INK}`,
      borderRadius: 999,
      padding: "14px 40px",
      boxShadow: `6px 6px 0 rgba(43,43,58,0.85)`,
      whiteSpace: "nowrap",
    }}
  >
    {text}
  </div>
);
