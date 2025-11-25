import { createContext } from "react";

export type Language = 'en' | 'es' | 'fr' | 'de' | 'pt' | 'auto';

export interface LanguageContextType {
    language: Language;
    setLanguage: (lang: Language) => void;
    t: (key: string) => string;
}

export const LanguageContext = createContext<LanguageContextType | undefined>(undefined);
