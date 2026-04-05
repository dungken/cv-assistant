import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../ui/DropdownMenu';
import { Button } from '../ui/Button';

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="flex items-center gap-2 h-9 px-3 rounded-xl hover:bg-white/5 border border-transparent hover:border-white/10 transition-all">
          <Globe className="w-4 h-4 text-text-secondary" />
          <span className="text-[11px] font-bold uppercase tracking-wider text-text-secondary">
            {i18n.language === 'vi' ? 'VI' : 'EN'}
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-32 bg-canvas-dark/95 backdrop-blur-xl border-white/5 shadow-2xl rounded-2xl p-1.5 animate-in fade-in zoom-in-95 duration-200">
        <DropdownMenuItem
          onClick={() => changeLanguage('vi')}
          className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium cursor-pointer transition-colors ${
            i18n.language === 'vi' ? 'bg-accent-primary/10 text-accent-primary' : 'text-text-secondary hover:bg-white/5'
          }`}
        >
          Tiếng Việt
          {i18n.language === 'vi' && <div className="w-1.5 h-1.5 rounded-full bg-accent-primary shadow-[0_0_8px_rgba(var(--accent-primary-rgb),0.6)]" />}
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => changeLanguage('en')}
          className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium cursor-pointer transition-colors ${
            i18n.language === 'en' ? 'bg-accent-primary/10 text-accent-primary' : 'text-text-secondary hover:bg-white/5'
          }`}
        >
          English
          {i18n.language === 'en' && <div className="w-1.5 h-1.5 rounded-full bg-accent-primary shadow-[0_0_8px_rgba(var(--accent-primary-rgb),0.6)]" />}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
