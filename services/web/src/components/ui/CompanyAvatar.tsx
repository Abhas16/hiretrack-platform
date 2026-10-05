import { avatarColor } from "@/lib/avatar";

interface CompanyAvatarProps {
  name: string;
  size?: number;
}

export function CompanyAvatar({ name, size = 36 }: CompanyAvatarProps) {
  return (
    <div
      aria-hidden="true"
      className="flex flex-none items-center justify-center rounded-[9px] font-bold text-white"
      style={{
        width: size,
        height: size,
        fontSize: Math.round(size * 0.42),
        background: avatarColor(name),
      }}
    >
      {name.charAt(0).toUpperCase()}
    </div>
  );
}
