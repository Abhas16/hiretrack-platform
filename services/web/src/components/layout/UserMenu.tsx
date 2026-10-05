import { Icon } from "@/components/ui/Icon";

import { THEME_OPTIONS, useUserMenuController } from "./useUserMenuController";

const ITEM =
  "flex w-full cursor-pointer items-center gap-3 rounded-lg border-0 bg-transparent px-3 py-2.5 text-left text-sm font-medium text-ink-2 no-underline hover:bg-canvas";

export function UserMenu() {
  const {
    rootRef,
    buttonRef,
    isOpen,
    toggle,
    name,
    email,
    initials,
    theme,
    setTheme,
    goToPractice,
    apiDocsUrl,
    buildInfo,
    signOut,
  } = useUserMenuController();

  return (
    <div ref={rootRef} className="relative">
      <button
        ref={buttonRef}
        type="button"
        onClick={toggle}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-label={name ? `Account menu for ${name}` : "Account menu"}
        className="text-muted flex cursor-pointer items-center gap-1 rounded-full border-0 bg-transparent p-0"
      >
        <span className="bg-accent flex size-10 items-center justify-center rounded-full text-sm font-bold text-white">
          {initials}
        </span>
        <Icon name="chevronDown" size={16} />
      </button>

      {isOpen && (
        <div
          role="menu"
          className="border-line bg-surface absolute top-12 right-0 z-30 flex w-72 flex-col gap-1 rounded-2xl border p-2 shadow-[0_16px_40px_rgba(18,21,28,0.18)]"
        >
          <div className="border-track flex items-center gap-3 border-b px-3 pt-2 pb-3">
            <span className="bg-accent flex size-10 flex-none items-center justify-center rounded-full text-sm font-bold text-white">
              {initials}
            </span>
            <div className="flex min-w-0 flex-col">
              <span className="truncate text-sm font-bold">{name}</span>
              <span className="text-muted truncate text-xs">{email}</span>
            </div>
          </div>

          <div className="text-muted px-3 pt-2 pb-1 text-xs font-semibold tracking-[0.6px] uppercase">
            Appearance
          </div>
          <div
            role="group"
            aria-label="Theme"
            className="bg-canvas mx-2 mb-1 grid grid-cols-3 gap-1 rounded-xl p-1"
          >
            {THEME_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                role="menuitemradio"
                aria-checked={theme === option.value}
                onClick={() => setTheme(option.value)}
                className={`flex cursor-pointer flex-col items-center gap-1 rounded-lg border-0 py-2 text-xs font-semibold ${
                  theme === option.value
                    ? "bg-surface text-ink shadow-sm"
                    : "text-muted hover:text-ink bg-transparent"
                }`}
              >
                <Icon name={option.icon} size={18} />
                {option.label}
              </button>
            ))}
          </div>

          <div className="border-track mt-1 flex flex-col border-t pt-1">
            <button type="button" role="menuitem" className={ITEM} onClick={goToPractice}>
              <Icon name="practice" size={18} /> Practice interview
            </button>
            {apiDocsUrl && (
              <a
                role="menuitem"
                className={ITEM}
                href={apiDocsUrl}
                target="_blank"
                rel="noreferrer noopener"
              >
                <Icon name="docs" size={18} /> API docs
              </a>
            )}
            <button
              type="button"
              role="menuitem"
              className={`${ITEM} text-danger`}
              onClick={signOut}
            >
              <Icon name="signOut" size={18} /> Sign out
            </button>
          </div>

          <div className="text-sidebar-faint px-3 pt-2 pb-1 font-mono text-[11px]">{buildInfo}</div>
        </div>
      )}
    </div>
  );
}
