import React, { useState } from "react";
import { LanguageContext } from "./LanguageCore";
import type { Language } from "./LanguageCore";

const translations: { [key: string]: { [lang: string]: string } } = {
    // Header
    'app.name': {
        en: 'Dux',
        es: 'Dux',
        fr: 'Dux',
        de: 'Dux',
        pt: 'Dux'
    },
    'header.logout': {
        en: 'Logout',
        es: 'Cerrar sesión',
        fr: 'Déconnexion',
        de: 'Abmelden',
        pt: 'Sair'
    },
    // Auth Page
    'auth.title': {
        en: 'Authentication',
        es: 'Autenticación',
        fr: 'Authentification',
        de: 'Authentifizierung',
        pt: 'Autenticação'
    },
    'auth.password': {
        en: 'Password',
        es: 'Contraseña',
        fr: 'Mot de passe',
        de: 'Passwort',
        pt: 'Senha'
    },
    'auth.passkey': {
        en: 'Passkey',
        es: 'Clave de acceso',
        fr: 'Clé d\'accès',
        de: 'Passkey',
        pt: 'Chave de acesso'
    },
    'auth.username': {
        en: 'Username',
        es: 'Usuario',
        fr: 'Nom d\'utilisateur',
        de: 'Benutzername',
        pt: 'Nome de usuário'
    },
    'auth.password.placeholder': {
        en: 'Password',
        es: 'Contraseña',
        fr: 'Mot de passe',
        de: 'Passwort',
        pt: 'Senha'
    },
    'auth.login': {
        en: 'Login',
        es: 'Iniciar sesión',
        fr: 'Se connecter',
        de: 'Anmelden',
        pt: 'Entrar'
    },
    'auth.register': {
        en: 'Register',
        es: 'Registrarse',
        fr: 'S\'inscrire',
        de: 'Registrieren',
        pt: 'Registrar'
    },
    'auth.logging_in': {
        en: 'Logging in...',
        es: 'Iniciando sesión...',
        fr: 'Connexion...',
        de: 'Anmeldung...',
        pt: 'Entrando...'
    },
    'auth.registering': {
        en: 'Registering...',
        es: 'Registrando...',
        fr: 'Inscription...',
        de: 'Registrierung...',
        pt: 'Registrando...'
    },
    'auth.already_account': {
        en: 'Already have an account? Login',
        es: '¿Ya tienes cuenta? Iniciar sesión',
        fr: 'Vous avez déjà un compte? Se connecter',
        de: 'Haben Sie bereits ein Konto? Anmelden',
        pt: 'Já tem uma conta? Entrar'
    },
    'auth.need_account': {
        en: 'Need an account? Register',
        es: '¿Necesitas una cuenta? Registrarse',
        fr: 'Besoin d\'un compte? S\'inscrire',
        de: 'Brauchen Sie ein Konto? Registrieren',
        pt: 'Precisa de uma conta? Registrar'
    },
    'auth.passkey.login': {
        en: 'Login with Passkey',
        es: 'Iniciar sesión con clave',
        fr: 'Se connecter avec clé',
        de: 'Mit Passkey anmelden',
        pt: 'Entrar com chave'
    },
    'auth.passkey.register': {
        en: 'Register New Passkey',
        es: 'Registrar nueva clave',
        fr: 'Enregistrer nouvelle clé',
        de: 'Neuen Passkey registrieren',
        pt: 'Registrar nova chave'
    },
    'auth.authenticating': {
        en: 'Authenticating...',
        es: 'Autenticando...',
        fr: 'Authentification...',
        de: 'Authentifizierung...',
        pt: 'Autenticando...'
    },
    // Home Page
    'home.welcome': {
        en: 'Welcome to Dux',
        es: 'Bienvenido a Dux',
        fr: 'Bienvenue sur Dux',
        de: 'Willkommen bei Dux',
        pt: 'Bem-vindo ao Dux'
    },
    'home.authenticated': {
        en: 'You are now authenticated and can access protected features.',
        es: 'Ahora estás autenticado y puedes acceder a funciones protegidas.',
        fr: 'Vous êtes maintenant authentifié et pouvez accéder aux fonctionnalités protégées.',
        de: 'Sie sind jetzt authentifiziert und können auf geschützte Funktionen zugreifen.',
        pt: 'Agora você está autenticado e pode acessar recursos protegidos.'
    },
    'home.account': {
        en: 'Account',
        es: 'Cuenta',
        fr: 'Compte',
        de: 'Konto',
        pt: 'Conta'
    },
    // Upload Page
    'upload.title': {
        en: 'Dux File Upload',
        es: 'Carga de archivos Dux',
        fr: 'Téléchargement de fichiers Dux',
        de: 'Dux Datei-Upload',
        pt: 'Upload de arquivos Dux'
    },
    'upload.button': {
        en: 'Upload',
        es: 'Subir',
        fr: 'Télécharger',
        de: 'Hochladen',
        pt: 'Enviar'
    },
    'upload.uploading': {
        en: 'Uploading...',
        es: 'Subiendo...',
        fr: 'Téléchargement...',
        de: 'Hochladen...',
        pt: 'Enviando...'
    },
    // Theme
    'theme.light': {
        en: 'Light mode',
        es: 'Modo claro',
        fr: 'Mode clair',
        de: 'Heller Modus',
        pt: 'Modo claro'
    },
    'theme.dark': {
        en: 'Dark mode',
        es: 'Modo oscuro',
        fr: 'Mode sombre',
        de: 'Dunkler Modus',
        pt: 'Modo escuro'
    },
    'theme.auto': {
        en: 'Auto (system)',
        es: 'Auto (sistema)',
        fr: 'Auto (système)',
        de: 'Auto (System)',
        pt: 'Auto (sistema)'
    },
    // Language
    'language.auto': {
        en: 'Auto (browser)',
        es: 'Auto (navegador)',
        fr: 'Auto (navigateur)',
        de: 'Auto (Browser)',
        pt: 'Auto (navegador)'
    }
};

// LanguageContext is now defined and exported from LanguageCore.ts

const detectBrowserLanguage = (): Exclude<Language, 'auto'> => {
    const browserLang = navigator.language.split('-')[0];
    const supportedLangs: Array<Exclude<Language, 'auto'>> = ['en', 'es', 'fr', 'de', 'pt'];
    return supportedLangs.includes(browserLang as Exclude<Language, 'auto'>)
        ? (browserLang as Exclude<Language, 'auto'>)
        : 'en';
};

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [language, setLanguageState] = useState<Language>(() => {
        const saved = localStorage.getItem('language') as Language;
        return saved || 'auto';
    });

    const setLanguage = React.useCallback((lang: Language) => {
        setLanguageState(lang);
        localStorage.setItem('language', lang);
    }, []);

    const t = React.useCallback((key: string): string => {
        const getCurrentLanguage = (): Exclude<Language, 'auto'> => {
            return language === 'auto' ? detectBrowserLanguage() : language as Exclude<Language, 'auto'>;
        };
        const currentLang = getCurrentLanguage();
        return translations[key]?.[currentLang] || translations[key]?.['en'] || key;
    }, [language]);

    const contextValue = React.useMemo(
        () => ({ language, setLanguage, t }),
        [language, setLanguage, t]
    );

    return (
        <LanguageContext.Provider value={contextValue}>
            {children}
        </LanguageContext.Provider>
    );
};
