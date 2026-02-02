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
        pt: 'Dux',
        la: 'Dux'
    },
    'header.logout': {
        en: 'Logout',
        es: 'Cerrar sesión',
        fr: 'Déconnexion',
        de: 'Abmelden',
        pt: 'Sair',
        la: 'Exire'
    },
    'header.menu': {
        en: 'Menu',
        es: 'Menú',
        fr: 'Menu',
        de: 'Menü',
        pt: 'Menu',
        la: 'Tabula'
    },
    'header.settings': {
        en: 'Settings',
        es: 'Configuración',
        fr: 'Paramètres',
        de: 'Einstellungen',
        pt: 'Configurações',
        la: 'Configurationes'
    },
    // Auth Page
    'auth.title': {
        en: 'Authentication',
        es: 'Autenticación',
        fr: 'Authentification',
        de: 'Authentifizierung',
        pt: 'Autenticação',
        la: 'Authentificatio'
    },
    'auth.password': {
        en: 'Password',
        es: 'Contraseña',
        fr: 'Mot de passe',
        de: 'Passwort',
        pt: 'Senha',
        la: 'Tessera'
    },
    'auth.passkey': {
        en: 'Passkey',
        es: 'Clave de acceso',
        fr: 'Clé d\'accès',
        de: 'Passkey',
        pt: 'Chave de acesso',
        la: 'Clavis Aditus'
    },
    'auth.username': {
        en: 'Username',
        es: 'Usuario',
        fr: 'Nom d\'utilisateur',
        de: 'Benutzername',
        pt: 'Nome de usuário',
        la: 'Nomen Usoris'
    },
    'auth.password.placeholder': {
        en: 'Password',
        es: 'Contraseña',
        fr: 'Mot de passe',
        de: 'Passwort',
        pt: 'Senha',
        la: 'Tessera'
    },
    'auth.login': {
        en: 'Login',
        es: 'Iniciar sesión',
        fr: 'Se connecter',
        de: 'Anmelden',
        pt: 'Entrar',
        la: 'Intrare'
    },
    'auth.register': {
        en: 'Register',
        es: 'Registrarse',
        fr: 'S\'inscrire',
        de: 'Registrieren',
        pt: 'Registrar',
        la: 'Inscribere'
    },
    'auth.logging_in': {
        en: 'Logging in...',
        es: 'Iniciando sesión...',
        fr: 'Connexion...',
        de: 'Anmeldung...',
        pt: 'Entrando...',
        la: 'Intrando...'
    },
    'auth.registering': {
        en: 'Registering...',
        es: 'Registrando...',
        fr: 'Inscription...',
        de: 'Registrierung...',
        pt: 'Registrando...',
        la: 'Inscribendo...'
    },
    'auth.already_account': {
        en: 'Already have an account? Login',
        es: '¿Ya tienes cuenta? Iniciar sesión',
        fr: 'Vous avez déjà un compte? Se connecter',
        de: 'Haben Sie bereits ein Konto? Anmelden',
        pt: 'Já tem uma conta? Entrar',
        la: 'Iam rationem habes? Intrare'
    },
    'auth.need_account': {
        en: 'Need an account? Register',
        es: '¿Necesitas una cuenta? Registrarse',
        fr: 'Besoin d\'un compte? S\'inscrire',
        de: 'Brauchen Sie ein Konto? Registrieren',
        pt: 'Precisa de uma conta? Registrar',
        la: 'Rationem necessitas? Inscribere'
    },
    'auth.passkey.login': {
        en: 'Login with Passkey',
        es: 'Iniciar sesión con clave',
        fr: 'Se connecter avec clé',
        de: 'Mit Passkey anmelden',
        pt: 'Entrar com chave',
        la: 'Intrare cum Clave'
    },
    'auth.passkey.register': {
        en: 'Register New Passkey',
        es: 'Registrar nueva clave',
        fr: 'Enregistrer nouvelle clé',
        de: 'Neuen Passkey registrieren',
        pt: 'Registrar nova chave',
        la: 'Inscribere Clavem Novam'
    },
    'auth.authenticating': {
        en: 'Authenticating...',
        es: 'Autenticando...',
        fr: 'Authentification...',
        de: 'Authentifizierung...',
        pt: 'Autenticando...',
        la: 'Authentificando...'
    },
    'auth.or': {
        en: 'or',
        es: 'o',
        fr: 'ou',
        de: 'oder',
        pt: 'ou',
        la: 'aut'
    },
    'auth.linkedin_signin': {
        en: 'Sign in with LinkedIn',
        es: 'Iniciar sesión con LinkedIn',
        fr: 'Se connecter avec LinkedIn',
        de: 'Mit LinkedIn anmelden',
        pt: 'Entrar com LinkedIn',
        la: 'Intrare cum LinkedIn'
    },
    'auth.registration_successful': {
        en: 'Registration successful! You can now log in.',
        es: '¡Registro exitoso! Ahora puedes iniciar sesión.',
        fr: 'Inscription réussie! Vous pouvez maintenant vous connecter.',
        de: 'Registrierung erfolgreich! Sie können sich jetzt anmelden.',
        pt: 'Registro bem-sucedido! Você pode fazer login agora.',
        la: 'Inscriptio feliciter peracta! Modo intrare potes.'
    },
    'auth.passkey_registered_success': {
        en: 'Passkey registered successfully! You can now log in.',
        es: '¡Clave registrada exitosamente! Ahora puedes iniciar sesión.',
        fr: 'Clé enregistrée avec succès! Vous pouvez maintenant vous connecter.',
        de: 'Passkey erfolgreich registriert! Sie können sich jetzt anmelden.',
        pt: 'Chave registrada com sucesso! Você pode fazer login agora.',
        la: 'Clavis feliciter inscripta! Modo intrare potes.'
    },
    // Home Page
    'home.welcome': {
        en: 'Welcome to Dux',
        es: 'Bienvenido a Dux',
        fr: 'Bienvenue sur Dux',
        de: 'Willkommen bei Dux',
        pt: 'Bem-vindo ao Dux',
        la: 'Salve ad Dux'
    },
    'home.welcome_intro': {
        en: 'Your AI-powered job search companion. Get started with these features:',
        es: 'Tu compañero de búsqueda de empleo impulsado por IA. Comienza con estas funciones:',
        fr: 'Votre assistant de recherche d\'emploi alimenté par l\'IA. Commencez avec ces fonctionnalités :',
        de: 'Ihr KI-gestützter Begleiter für die Jobsuche. Beginnen Sie mit diesen Funktionen:',
        pt: 'Seu companheiro de busca de emprego com IA. Comece com esses recursos:',
        la: 'Socius tuus quaerendi operis per AI. Incipe his functionibus:'
    },
    'home.feature_cv_title': {
        en: 'CV Analysis',
        es: 'Análisis de CV',
        fr: 'Analyse de CV',
        de: 'Lebenslauf-Analyse',
        pt: 'Análise de Currículo',
        la: 'Analysis CV'
    },
    'home.feature_cv_desc': {
        en: 'Upload your CV to get AI-powered insights and improvement suggestions.',
        es: 'Sube tu CV para obtener información y sugerencias de mejora impulsadas por IA.',
        fr: 'Téléchargez votre CV pour obtenir des informations et suggestions d\'amélioration par IA.',
        de: 'Laden Sie Ihren Lebenslauf hoch, um KI-gestützte Einblicke und Verbesserungsvorschläge zu erhalten.',
        pt: 'Carregue seu currículo para obter insights e sugestões de melhoria com IA.',
        la: 'Transfer CV tuum ut consilium et suggestiones meliorationis per AI habeas.'
    },
    'home.feature_jobs_title': {
        en: 'Smart Job Matching',
        es: 'Emparejamiento Inteligente de Trabajos',
        fr: 'Correspondance Intelligente d\'Emplois',
        de: 'Intelligente Job-Matching',
        pt: 'Correspondência Inteligente de Vagas',
        la: 'Comparatio Intelligens Operum'
    },
    'home.feature_jobs_desc': {
        en: 'Browse jobs tailored to your profile with AI-powered match scores.',
        es: 'Explora trabajos adaptados a tu perfil con puntuaciones de coincidencia impulsadas por IA.',
        fr: 'Parcourez les emplois adaptés à votre profil avec des scores de correspondance par IA.',
        de: 'Durchsuchen Sie Jobs, die auf Ihr Profil zugeschnitten sind, mit KI-gestützten Match-Scores.',
        pt: 'Navegue por vagas adaptadas ao seu perfil com pontuações de correspondência com IA.',
        la: 'Perlustra opera ad professionem tuam accommodata cum punctis comparationis per AI.'
    },
    'home.feature_analysis_title': {
        en: 'Job Insights',
        es: 'Perspectivas de Trabajo',
        fr: 'Informations sur les Emplois',
        de: 'Job-Einblicke',
        pt: 'Insights de Vagas',
        la: 'Perspicacia Operum'
    },
    'home.feature_analysis_desc': {
        en: 'Get detailed analysis of how your profile matches each job opportunity.',
        es: 'Obtén análisis detallados de cómo tu perfil coincide con cada oportunidad laboral.',
        fr: 'Obtenez une analyse détaillée de la correspondance de votre profil avec chaque opportunité.',
        de: 'Erhalten Sie detaillierte Analysen darüber, wie Ihr Profil zu jeder Jobmöglichkeit passt.',
        pt: 'Obtenha análises detalhadas de como seu perfil corresponde a cada oportunidade.',
        la: 'Accipe analysim detailem quomodo professio tua cum unaquaque opportunitate congruat.'
    },
    'home.explore_jobs': {
        en: 'Explore Jobs',
        es: 'Explorar Trabajos',
        fr: 'Explorer les Emplois',
        de: 'Jobs Erkunden',
        pt: 'Explorar Vagas',
        la: 'Explora Opera'
    },
    'home.authenticated': {
        en: 'You are now authenticated and can access protected features.',
        es: 'Ahora estás autenticado y puedes acceder a funciones protegidas.',
        fr: 'Vous êtes maintenant authentifié et pouvez accéder aux fonctionnalités protégées.',
        de: 'Sie sind jetzt authentifiziert und können auf geschützte Funktionen zugreifen.',
        pt: 'Agora você está autenticado e pode acessar recursos protegidos.',
        la: 'Nunc authentificatus es et functiones protectas adire potes.'
    },
    'home.account': {
        en: 'Account',
        es: 'Cuenta',
        fr: 'Compte',
        de: 'Konto',
        pt: 'Conta',
        la: 'Ratio'
    },
    'home.cv_title': {
        en: 'Your CV on file',
        es: 'Tu CV guardado',
        fr: 'Votre CV enregistré',
        de: 'Dein gespeichertes CV',
        pt: 'Seu CV armazenado',
        la: 'Curriculum tuum retentum'
    },
    'home.cv_missing': {
        en: 'No CV uploaded yet. Upload a PDF to preview it here.',
        es: 'Aún no subiste un CV. Sube un PDF para verlo aquí.',
        fr: 'Aucun CV téléversé pour le moment. Ajoutez un PDF pour l\'afficher ici.',
        de: 'Noch kein CV hochgeladen. Lade ein PDF hoch, um es hier zu sehen.',
        pt: 'Nenhum CV enviado ainda. Envie um PDF para pré-visualizar aqui.',
        la: 'Nondum curriculum sublatum. PDF mitte ut hic praevideas.'
    },
    'home.cv_open_link': {
        en: 'Open CV in a new tab',
        es: 'Abrir CV en una nueva pestaña',
        fr: 'Ouvrir le CV dans un nouvel onglet',
        de: 'CV in neuem Tab öffnen',
        pt: 'Abrir o CV em nova aba',
        la: 'Curriculum in nova scheda aperire'
    },
    'home.cv_preview_unavailable': {
        en: 'We couldn\'t load the preview.',
        es: 'No pudimos cargar la vista previa.',
        fr: 'Impossible de charger l\'aperçu.',
        de: 'Vorschau konnte nicht geladen werden.',
        pt: 'Não foi possível carregar a pré-visualização.',
        la: 'Praevisio onerari non potuit.'
    },
    // Upload Page
    'upload.title': {
        en: 'Dux File Upload',
        es: 'Carga de archivos Dux',
        fr: 'Téléchargement de fichiers Dux',
        de: 'Dux Datei-Upload',
        pt: 'Upload de arquivos Dux',
        la: 'Dux Fasciculi Sumptio'
    },
    'upload.button': {
        en: 'Upload',
        es: 'Subir',
        fr: 'Télécharger',
        de: 'Hochladen',
        pt: 'Enviar',
        la: 'Mittere'
    },
    'upload.uploading': {
        en: 'Uploading...',
        es: 'Subiendo...',
        fr: 'Téléchargement...',
        de: 'Hochladen...',
        pt: 'Enviando...',
        la: 'Mittendo...'
    },
    'upload.no_file_selected': {
        en: 'Please select a file to upload.',
        es: 'Por favor, selecciona un archivo para subir.',
        fr: 'Veuillez sélectionner un fichier à télécharger.',
        de: 'Bitte wählen Sie eine Datei zum Hochladen aus.',
        pt: 'Por favor, selecione um arquivo para enviar.',
        la: 'Elige fasciculum mittendum.'
    },
    'upload.failed': {
        en: 'Upload failed',
        es: 'La subida falló',
        fr: 'Le téléchargement a échoué',
        de: 'Upload fehlgeschlagen',
        pt: 'Upload falhou',
        la: 'Sumptio defecit'
    },
    'upload.success': {
        en: 'File uploaded successfully!',
        es: '¡Archivo subido exitosamente!',
        fr: 'Fichier téléchargé avec succès!',
        de: 'Datei erfolgreich hochgeladen!',
        pt: 'Arquivo enviado com sucesso!',
        la: 'Fasciculus feliciter sublatus!'
    },
    // Theme
    'theme.light': {
        en: 'Light mode',
        es: 'Modo claro',
        fr: 'Mode clair',
        de: 'Heller Modus',
        pt: 'Modo claro',
        la: 'Modus Lucis'
    },
    'theme.dark': {
        en: 'Dark mode',
        es: 'Modo oscuro',
        fr: 'Mode sombre',
        de: 'Dunkler Modus',
        pt: 'Modo escuro',
        la: 'Modus Tenebrae'
    },
    'theme.auto': {
        en: 'Auto (system)',
        es: 'Auto (sistema)',
        fr: 'Auto (système)',
        de: 'Auto (System)',
        pt: 'Auto (sistema)',
        la: 'Auto (systema)'
    },
    // Language
    'language.auto': {
        en: 'Auto (browser)',
        es: 'Auto (navegador)',
        fr: 'Auto (navigateur)',
        de: 'Auto (Browser)',
        pt: 'Auto (navegador)',
        la: 'Auto (navigator)'
    },
    // LinkedIn Integration
    'linkedin.populate': {
        en: 'Populate with LinkedIn',
        es: 'Rellenar con LinkedIn',
        fr: 'Remplir avec LinkedIn',
        de: 'Mit LinkedIn ausfüllen',
        pt: 'Preencher com LinkedIn',
        la: 'Implere cum LinkedIn'
    },
    'linkedin.connecting': {
        en: 'Connecting to LinkedIn...',
        es: 'Conectando con LinkedIn...',
        fr: 'Connexion à LinkedIn...',
        de: 'Verbindung zu LinkedIn...',
        pt: 'Conectando ao LinkedIn...',
        la: 'Conectendo ad LinkedIn...'
    },
    'linkedin.success': {
        en: 'Profile updated successfully!',
        es: '¡Perfil actualizado exitosamente!',
        fr: 'Profil mis à jour avec succès!',
        de: 'Profil erfolgreich aktualisiert!',
        pt: 'Perfil atualizado com sucesso!',
        la: 'Profilus feliciter renovatus!'
    },
    'linkedin.error': {
        en: 'Failed to connect to LinkedIn',
        es: 'Error al conectar con LinkedIn',
        fr: 'Échec de connexion à LinkedIn',
        de: 'LinkedIn-Verbindung fehlgeschlagen',
        pt: 'Falha ao conectar ao LinkedIn',
        la: 'Conectio ad LinkedIn defecit'
    },
    // Metiers / Wiki
    'metiers.sidebar_title': {
        en: 'Professions',
        es: 'Profesiones',
        fr: 'Métiers',
        de: 'Berufe',
        pt: 'Profissões',
        la: 'Artes'
    },
    'metiers.search_placeholder': {
        en: 'Search a job (ROME or label)',
        es: 'Buscar un oficio (ROME o etiqueta)',
        fr: 'Rechercher un metier (ROME ou libelle)',
        de: 'Beruf suchen (ROME oder Bezeichnung)',
        pt: 'Pesquisar uma profissao (ROME ou rotulo)',
        la: 'Artem quaerere (ROME vel titulus)'
    },
    'metiers.loading': {
        en: 'Loading...',
        es: 'Cargando...',
        fr: 'Chargement...',
        de: 'Laedt...',
        pt: 'Carregando...',
        la: 'Oneratur...'
    },
    'metiers.no_results': {
        en: 'No results.',
        es: 'Sin resultados.',
        fr: 'Aucun résultat.',
        de: 'Keine Ergebnisse.',
        pt: 'Nenhum resultado.',
        la: 'Nulla resultata.'
    },
    'metiers.select_prompt': {
        en: 'Select a job to display the detail.',
        es: 'Selecciona un oficio para ver la ficha.',
        fr: 'Sélectionnez un métier pour afficher la fiche.',
        de: 'Waehle einen Beruf, um die Details anzuzeigen.',
        pt: 'Selecione uma profissao para ver a ficha.',
        la: 'Artem elige ut schedam videas.'
    },
    'metiers.detail.loading': {
        en: 'Loading job...',
        es: 'Cargando oficio...',
        fr: 'Chargement du métier...',
        de: 'Beruf wird geladen...',
        pt: 'Carregando profissao...',
        la: 'Ars oneratur...'
    },
    'metiers.detail.no_data': {
        en: 'No data available.',
        es: 'No hay datos disponibles.',
        fr: 'Aucune donnée disponible.',
        de: 'Keine Daten verfuegbar.',
        pt: 'Nenhum dado disponivel.',
        la: 'Nulla data praesto.'
    },
    'metiers.detail.summary_fallback': {
        en: 'Description not available for this job.',
        es: 'Descripcion no disponible para este oficio.',
        fr: 'Description non disponible pour ce métier.',
        de: 'Beschreibung fuer diesen Beruf nicht verfuegbar.',
        pt: 'Descricao nao disponível para esta profissao.',
        la: 'Descriptio huius artis non praesto.'
    },
    'metiers.detail.title_fallback': {
        en: 'Job detail',
        es: 'Detalle del oficio',
        fr: 'Détail métier',
        de: 'Berufsdetails',
        pt: 'Detalhe da profissao',
        la: 'Detalia artis'
    },
    'metiers.detail.title_cv_comparison': {
        en: 'CV Comparison',
        es: 'Comparación de CV',
        fr: 'Comparaison du CV',
        de: 'Lebenslaufvergleich',
        pt: 'Comparação de currículos',
        la: 'CV Comparatio'
    },
    'metiers.detail.key_metrics': {
        en: 'Key metrics',
        es: 'Indicadores clave',
        fr: 'Indicateurs clés',
        de: 'Schluesselkennzahlen',
        pt: 'Indicadores chave',
        la: 'Indicia praecipua'
    },
    'metiers.detail.stats.offers': {
        en: 'Offers',
        es: 'Ofertas',
        fr: 'Offres',
        de: 'Angebote',
        pt: 'Ofertas',
        la: 'Offerta'
    },
    'metiers.detail.stats.offers_active': {
        en: 'active offers',
        es: 'ofertas activas',
        fr: 'offres actives',
        de: 'aktive Angebote',
        pt: 'ofertas ativas',
        la: 'offerta activa'
    },
    'metiers.detail.stats.avg_salary': {
        en: 'Average salary',
        es: 'Salario medio',
        fr: 'Salaire moyen',
        de: 'Durchschnittsgehalt',
        pt: 'Salario medio',
        la: 'Merces media'
    },
    'metiers.detail.stats.monthly': {
        en: 'monthly',
        es: 'mensual',
        fr: 'mensuel',
        de: 'monatlich',
        pt: 'mensal',
        la: 'menstruus'
    },
    'metiers.detail.stats.range': {
        en: 'Range',
        es: 'Rango',
        fr: 'Fourchette',
        de: 'Spanne',
        pt: 'Faixa',
        la: 'Spatium'
    },
    'metiers.detail.stats.min_max': {
        en: 'min / max',
        es: 'min / max',
        fr: 'min / max',
        de: 'min / max',
        pt: 'min / max',
        la: 'min / max'
    },
    'metiers.detail.salary_range_title': {
        en: 'Salary range (monthly)',
        es: 'Rango salarial (mensual)',
        fr: 'Fourchette de salaire (mensuel)',
        de: 'Gehaltsspanne (monatlich)',
        pt: 'Faixa salarial (mensal)',
        la: 'Spatium mercedis (menstruum)'
    },
    'metiers.detail.salary_mean': {
        en: 'Average salary',
        es: 'Salario medio',
        fr: 'Salaire moyen',
        de: 'Durchschnittsgehalt',
        pt: 'Salario medio',
        la: 'Merces media'
    },
    'metiers.detail.salary_no_data': {
        en: 'No salary data available.',
        es: 'No hay datos salariales disponibles.',
        fr: 'Aucune donnée de salaire disponible.',
        de: 'Keine Gehaltsdaten verfuegbar.',
        pt: 'Nenhum dado salarial disponivel.',
        la: 'Data mercedis non praesto.'
    },
    'metiers.detail.role_title': {
        en: 'Role and main missions',
        es: 'Rol y misiones principales',
        fr: 'Role et missions principales',
        de: 'Rolle und Hauptaufgaben',
        pt: 'Funcao e principais missoes',
        la: 'Munus et officia principalia'
    },
    'metiers.detail.description_missing': {
        en: 'No description available.',
        es: 'No hay descripcion disponible.',
        fr: 'Aucune description disponible.',
        de: 'Keine Beschreibung verfuegbar.',
        pt: 'Nenhuma descricao disponivel.',
        la: 'Descriptio non praesto.'
    },
    'metiers.detail.see_more': {
        en: 'See more',
        es: 'Ver mas',
        fr: 'Voir plus',
        de: 'Mehr anzeigen',
        pt: 'Ver mais',
        la: 'Plus videre'
    },
    'metiers.detail.see_less': {
        en: 'See less',
        es: 'Ver menos',
        fr: 'Voir moins',
        de: 'Weniger anzeigen',
        pt: 'Ver menos',
        la: 'Minus videre'
    },
    'metiers.detail.training_access_title': {
        en: 'Training access',
        es: 'Acceso a la formacion',
        fr: 'Accès a la formation',
        de: 'Zugang zur Weiterbildung',
        pt: 'Acesso a formacao',
        la: 'Aditus ad formationem'
    },
    'metiers.detail.skills_title': {
        en: 'Skills',
        es: 'Competencias',
        fr: 'Compétences',
        de: 'Kompetenzen',
        pt: 'Competencias',
        la: 'Peritiae'
    },
    'metiers.detail.skills_empty': {
        en: 'No skills provided.',
        es: 'No hay competencias registradas.',
        fr: 'Aucune compétence renseignée.',
        de: 'Keine Kompetenzen vorhanden.',
        pt: 'Nenhuma competencia informada.',
        la: 'Nullae peritiae praestitae.'
    },
    'metiers.detail.actions_title': {
        en: 'Actions',
        es: 'Acciones',
        fr: 'Actions',
        de: 'Aktionen',
        pt: 'Acoes',
        la: 'Actiones'
    },
    'metiers.detail.action_offers': {
        en: 'See related offers',
        es: 'Ver ofertas relacionadas',
        fr: 'Voir les offres liees',
        de: 'Verwandte Angebote anzeigen',
        pt: 'Ver ofertas relacionadas',
        la: 'Offertas cognatas videre'
    },
    'metiers.detail.action_compare_cv': {
        en: 'Compare with my CV',
        es: 'Comparar con mi CV',
        fr: 'Comparer avec mon CV',
        de: 'Mit meinem Lebenslauf vergleichen',
        pt: 'Comparar com meu CV',
        la: 'Cum CV meo comparare'
    },
    'metiers.detail.action_favorite': {
        en: 'Add to favorites',
        es: 'Anadir a favoritos',
        fr: 'Ajouter aux favoris',
        de: 'Zu Favoriten hinzufuegen',
        pt: 'Adicionar aos favoritos',
        la: 'Ad gratissima addere'
    },
    'metiers.detail.action_unfavorite': {
        en: 'Remove from favorites',
        es: 'Quitar de favoritos',
        fr: 'Retirer des favoris',
        de: 'Aus Favoriten entfernen',
        pt: 'Remover dos favoritos',
        la: 'E gratissimis removere'
    },
    'metiers.detail.error_unknown': {
        en: 'Unknown error',
        es: 'Error desconocido',
        fr: 'Erreur inconnue',
        de: 'Unbekannter Fehler',
        pt: 'Erro desconhecido',
        la: 'Error ignotus'
    },
    // Job Search
    'jobs.title': {
        en: 'Job Search',
        es: 'Búsqueda de Empleo',
        fr: 'Recherche d\'Emploi',
        de: 'Stellensuche',
        pt: 'Busca de Emprego',
        la: 'Quaestio Operis'
    },
    'jobs.search_placeholder': {
        en: 'Search by title, company, or keywords...',
        es: 'Buscar por título, empresa o palabras clave...',
        fr: 'Rechercher par titre, entreprise ou mots-clés...',
        de: 'Nach Titel, Firma oder Stichwörtern suchen...',
        pt: 'Pesquisar por título, empresa ou palavras-chave...',
        la: 'Quaerere per titulum, societatem, vel verba clavis...'
    },
    'jobs.location_filter': {
        en: 'Location',
        es: 'Ubicación',
        fr: 'Localisation',
        de: 'Standort',
        pt: 'Localização',
        la: 'Locus'
    },
    'jobs.type_all': {
        en: 'All Job Types',
        es: 'Todos los Tipos',
        fr: 'Tous les Types',
        de: 'Alle Typen',
        pt: 'Todos os Tipos',
        la: 'Omnes Species'
    },
    'jobs.type_fulltime': {
        en: 'Full-time',
        es: 'Tiempo completo',
        fr: 'Temps plein',
        de: 'Vollzeit',
        pt: 'Tempo integral',
        la: 'Tempus Plenum'
    },
    'jobs.type_parttime': {
        en: 'Part-time',
        es: 'Tiempo parcial',
        fr: 'Temps partiel',
        de: 'Teilzeit',
        pt: 'Meio período',
        la: 'Tempus Partiale'
    },
    'jobs.type_contract': {
        en: 'Contract',
        es: 'Contrato',
        fr: 'Contrat',
        de: 'Vertrag',
        pt: 'Contrato',
        la: 'Contractus'
    },
    'jobs.type_internship': {
        en: 'Internship',
        es: 'Pasantía',
        fr: 'Stage',
        de: 'Praktikum',
        pt: 'Estágio',
        la: 'Tirocinium'
    },
    'jobs.remote_only': {
        en: 'Remote only',
        es: 'Solo remoto',
        fr: 'À distance uniquement',
        de: 'Nur Remote',
        pt: 'Apenas remoto',
        la: 'Longinquum solum'
    },
    'jobs.remote': {
        en: 'Remote',
        es: 'Remoto',
        fr: 'À distance',
        de: 'Remote',
        pt: 'Remoto',
        la: 'Longinquum'
    },
    'jobs.clear_filters': {
        en: 'Clear all filters',
        es: 'Limpiar filtros',
        fr: 'Effacer les filtres',
        de: 'Filter löschen',
        pt: 'Limpar filtros',
        la: 'Purgare colationes'
    },
    'jobs.results_count': {
        en: '{count} jobs found',
        es: '{count} empleos encontrados',
        fr: '{count} emplois trouvés',
        de: '{count} Stellen gefunden',
        pt: '{count} vagas encontradas',
        la: '{count} opera inventa'
    },
    'jobs.no_results': {
        en: 'No jobs found matching your criteria',
        es: 'No se encontraron empleos que coincidan',
        fr: 'Aucun emploi trouvé correspondant',
        de: 'Keine passenden Stellen gefunden',
        pt: 'Nenhuma vaga encontrada',
        la: 'Nulla opera inventa'
    },
    'jobs.apply': {
        en: 'Apply Now',
        es: 'Aplicar Ahora',
        fr: 'Postuler Maintenant',
        de: 'Jetzt Bewerben',
        pt: 'Candidatar Agora',
        la: 'Applicare Nunc'
    },
    'jobs.posted_today': {
        en: 'Posted today',
        es: 'Publicado hoy',
        fr: 'Publié aujourd\'hui',
        de: 'Heute veröffentlicht',
        pt: 'Publicado hoje',
        la: 'Hodie publicatum'
    },
    'jobs.posted_days_ago': {
        en: 'Posted {days} days ago',
        es: 'Publicado hace {days} días',
        fr: 'Publié il y a {days} jours',
        de: 'Vor {days} Tagen veröffentlicht',
        pt: 'Publicado há {days} dias',
        la: 'Ante {days} dies publicatum'
    },
    'jobs.posted_weeks_ago': {
        en: 'Posted {weeks} weeks ago',
        es: 'Publicado hace {weeks} semanas',
        fr: 'Publié il y a {weeks} semaines',
        de: 'Vor {weeks} Wochen veröffentlicht',
        pt: 'Publicado há {weeks} semanas',
        la: 'Ante {weeks} hebdomadas publicatum'
    },
    'jobs.keywords': {
        en: 'Keywords',
        es: 'Palabras clave',
        fr: 'Mots-clés',
        de: 'Schlüsselwörter',
        pt: 'Palavras-chave',
        la: 'Verba Clavis'
    },
    'jobs.keywords_placeholder': {
        en: 'e.g., Developer, Project Manager...',
        es: 'Ej: Desarrollador, Director de Proyecto...',
        fr: 'Ex: Développeur, Chef de projet...',
        de: 'z.B. Entwickler, Projektmanager...',
        pt: 'Ex: Desenvolvedor, Gerente de Projeto...',
        la: 'Exempli gratia: Programmator, Magister Operis...'
    },
    'jobs.location': {
        en: 'Location',
        es: 'Ubicación',
        fr: 'Localisation',
        de: 'Standort',
        pt: 'Localização',
        la: 'Locus'
    },
    'jobs.commune': {
        en: 'Municipality (INSEE Code)',
        es: 'Municipio (Código INSEE)',
        fr: 'Commune (Code INSEE)',
        de: 'Gemeinde (INSEE-Code)',
        pt: 'Município (Código INSEE)',
        la: 'Municipium (Codex INSEE)'
    },
    'jobs.commune_placeholder': {
        en: 'e.g., 75056',
        es: 'Ej: 75056',
        fr: 'Ex: 75056',
        de: 'z.B. 75056',
        pt: 'Ex: 75056',
        la: 'Exempli gratia: 75056'
    },
    'jobs.department': {
        en: 'Department (Code)',
        es: 'Departamento (Código)',
        fr: 'Département (Code)',
        de: 'Departement (Code)',
        pt: 'Departamento (Código)',
        la: 'Departamentum (Codex)'
    },
    'jobs.department_placeholder': {
        en: 'e.g., 75 (2-digit code)',
        es: 'Ej: 75 (código de 2 dígitos)',
        fr: 'Ex: 75 (code 2 chiffres)',
        de: 'z.B. 75 (2-stelliger Code)',
        pt: 'Ex: 75 (código de 2 dígitos)',
        la: 'Exempli gratia: 75 (codex binis digitis)'
    },
    'jobs.region': {
        en: 'Region (Code)',
        es: 'Región (Código)',
        fr: 'Région (Code)',
        de: 'Region (Code)',
        pt: 'Região (Código)',
        la: 'Regio (Codex)'
    },
    'jobs.region_placeholder': {
        en: 'e.g., 11',
        es: 'Ej: 11',
        fr: 'Ex: 11',
        de: 'z.B. 11',
        pt: 'Ex: 11',
        la: 'Exempli gratia: 11'
    },
    'jobs.distance': {
        en: 'Distance (km)',
        es: 'Distancia (km)',
        fr: 'Distance (km)',
        de: 'Entfernung (km)',
        pt: 'Distância (km)',
        la: 'Distantia (km)'
    },
    'jobs.distance_placeholder': {
        en: 'e.g., 10',
        es: 'Ej: 10',
        fr: 'Ex: 10',
        de: 'z.B. 10',
        pt: 'Ex: 10',
        la: 'Exempli gratia: 10'
    },
    'jobs.contract_type': {
        en: 'Contract Type',
        es: 'Tipo de Contrato',
        fr: 'Type de contrat',
        de: 'Vertragsart',
        pt: 'Tipo de Contrato',
        la: 'Species Contractus'
    },
    'jobs.all_types': {
        en: 'All types',
        es: 'Todos los tipos',
        fr: 'Tous les types',
        de: 'Alle Arten',
        pt: 'Todos os tipos',
        la: 'Omnes species'
    },
    'jobs.contract_cdi': {
        en: 'Permanent (CDI)',
        es: 'Indefinido (CDI)',
        fr: 'CDI',
        de: 'Unbefristet (CDI)',
        pt: 'Efetivo (CDI)',
        la: 'Permanens (CDI)'
    },
    'jobs.contract_cdd': {
        en: 'Fixed-term (CDD)',
        es: 'Temporal (CDD)',
        fr: 'CDD',
        de: 'Befristet (CDD)',
        pt: 'Temporário (CDD)',
        la: 'Temporarius (CDD)'
    },
    'jobs.contract_mis': {
        en: 'Temporary (MIS)',
        es: 'Interino (MIS)',
        fr: 'MIS (Mission intérimaire)',
        de: 'Zeitarbeit (MIS)',
        pt: 'Temporário (MIS)',
        la: 'Interimarius (MIS)'
    },
    'jobs.contract_sai': {
        en: 'Seasonal (SAI)',
        es: 'Estacional (SAI)',
        fr: 'SAI (Saisonnier)',
        de: 'Saisonal (SAI)',
        pt: 'Sazonal (SAI)',
        la: 'Sesonalis (SAI)'
    },
    'jobs.contract_lib': {
        en: 'Freelance (LIB)',
        es: 'Autónomo (LIB)',
        fr: 'LIB (Libéral)',
        de: 'Freiberuflich (LIB)',
        pt: 'Autônomo (LIB)',
        la: 'Liberalis (LIB)'
    },
    'jobs.contract_rep': {
        en: 'Takeover/Succession (REP)',
        es: 'Sucesión (REP)',
        fr: 'REP (Reprise/Succession)',
        de: 'Übernahme/Nachfolge (REP)',
        pt: 'Sucessão (REP)',
        la: 'Successio (REP)'
    },
    'jobs.contract_fra': {
        en: 'Franchise (FRA)',
        es: 'Franquicia (FRA)',
        fr: 'FRA (Franchise)',
        de: 'Franchise (FRA)',
        pt: 'Franquia (FRA)',
        la: 'Franchisia (FRA)'
    },
    'jobs.contract_cce': {
        en: 'Project Contract (CCE)',
        es: 'Contrato de Obra (CCE)',
        fr: 'CCE (Contrat de chantier)',
        de: 'Baustellenvertrag (CCE)',
        pt: 'Contrato de Obra (CCE)',
        la: 'Contractus Operis (CCE)'
    },
    'jobs.contract_cpe': {
        en: 'Professional Contract (CPE)',
        es: 'Contrato Profesional (CPE)',
        fr: 'CPE (Contrat de professionnalisation)',
        de: 'Berufsvertrag (CPE)',
        pt: 'Contrato Profissional (CPE)',
        la: 'Contractus Professionalis (CPE)'
    },
    'jobs.experience_level': {
        en: 'Experience Level',
        es: 'Nivel de Experiencia',
        fr: 'Niveau d\'expérience',
        de: 'Erfahrungsniveau',
        pt: 'Nível de Experiência',
        la: 'Gradus Experientiae'
    },
    'jobs.all_levels': {
        en: 'All levels',
        es: 'Todos los niveles',
        fr: 'Tous niveaux',
        de: 'Alle Stufen',
        pt: 'Todos os níveis',
        la: 'Omnes gradus'
    },
    'jobs.experience_beginner': {
        en: 'Beginner accepted',
        es: 'Se acepta principiante',
        fr: 'Débutant accepté',
        de: 'Anfänger akzeptiert',
        pt: 'Iniciante aceito',
        la: 'Incipiens acceptus'
    },
    'jobs.experience_1_3': {
        en: '1 to 3 years',
        es: '1 a 3 años',
        fr: '1 à 3 ans',
        de: '1 bis 3 Jahre',
        pt: '1 a 3 anos',
        la: '1 ad 3 annos'
    },
    'jobs.experience_3_plus': {
        en: '3 years and more',
        es: '3 años y más',
        fr: '3 ans et plus',
        de: '3 Jahre und mehr',
        pt: '3 anos e mais',
        la: '3 annos et plus'
    },
    'jobs.qualification': {
        en: 'Qualification',
        es: 'Cualificación',
        fr: 'Qualification',
        de: 'Qualifikation',
        pt: 'Qualificação',
        la: 'Qualificatio'
    },
    'jobs.all': {
        en: 'All',
        es: 'Todos',
        fr: 'Tous',
        de: 'Alle',
        pt: 'Todos',
        la: 'Omnes'
    },
    'jobs.non_executive': {
        en: 'Non-executive',
        es: 'No ejecutivo',
        fr: 'Non cadre',
        de: 'Nicht leitend',
        pt: 'Não executivo',
        la: 'Non cadrus'
    },
    'jobs.executive': {
        en: 'Executive',
        es: 'Ejecutivo',
        fr: 'Cadre',
        de: 'Leitend',
        pt: 'Executivo',
        la: 'Cadrus'
    },
    'jobs.time_type': {
        en: 'Full/Part Time',
        es: 'Tiempo completo/parcial',
        fr: 'Temps plein / partiel',
        de: 'Vollzeit/Teilzeit',
        pt: 'Tempo integral/parcial',
        la: 'Tempus Plenum/Partiale'
    },
    'jobs.min_salary': {
        en: 'Minimum Salary (€)',
        es: 'Salario Mínimo (€)',
        fr: 'Salaire minimum (€)',
        de: 'Mindestgehalt (€)',
        pt: 'Salário Mínimo (€)',
        la: 'Salarium Minimum (€)'
    },
    'jobs.min_salary_placeholder': {
        en: 'e.g., 30000',
        es: 'Ej: 30000',
        fr: 'Ex: 30000',
        de: 'z.B. 30000',
        pt: 'Ex: 30000',
        la: 'Exempli gratia: 30000'
    },
    'jobs.published_since': {
        en: 'Published Since',
        es: 'Publicado Desde',
        fr: 'Publiée depuis',
        de: 'Veröffentlicht Seit',
        pt: 'Publicado Desde',
        la: 'Publicatum Ex'
    },
    'jobs.all_dates': {
        en: 'All dates',
        es: 'Todas las fechas',
        fr: 'Toutes les dates',
        de: 'Alle Daten',
        pt: 'Todas as datas',
        la: 'Omnes dies'
    },
    'jobs.today': {
        en: 'Today',
        es: 'Hoy',
        fr: 'Aujourd\'hui',
        de: 'Heute',
        pt: 'Hoje',
        la: 'Hodie'
    },
    'jobs.last_3_days': {
        en: 'Last 3 days',
        es: 'Últimos 3 días',
        fr: '3 derniers jours',
        de: 'Letzte 3 Tage',
        pt: 'Últimos 3 dias',
        la: 'Ultimi 3 dies'
    },
    'jobs.last_7_days': {
        en: 'Last 7 days',
        es: 'Últimos 7 días',
        fr: '7 derniers jours',
        de: 'Letzte 7 Tage',
        pt: 'Últimos 7 dias',
        la: 'Ultimi 7 dies'
    },
    'jobs.last_14_days': {
        en: 'Last 14 days',
        es: 'Últimos 14 días',
        fr: '14 derniers jours',
        de: 'Letzte 14 Tage',
        pt: 'Últimos 14 dias',
        la: 'Ultimi 14 dies'
    },
    'jobs.last_30_days': {
        en: 'Last 30 days',
        es: 'Últimos 30 días',
        fr: '30 derniers jours',
        de: 'Letzte 30 Tage',
        pt: 'Últimos 30 dias',
        la: 'Ultimi 30 dies'
    },
    'jobs.rome_code': {
        en: 'ROME Code',
        es: 'Código ROME',
        fr: 'Code ROME',
        de: 'ROME-Code',
        pt: 'Código ROME',
        la: 'Codex ROME'
    },
    'jobs.rome_code_placeholder': {
        en: 'e.g., M1805',
        es: 'Ej: M1805',
        fr: 'Ex: M1805',
        de: 'z.B. M1805',
        pt: 'Ex: M1805',
        la: 'Exempli gratia: M1805'
    },
    'jobs.sector': {
        en: 'Industry Sector',
        es: 'Sector de Actividad',
        fr: 'Secteur d\'activité',
        de: 'Branche',
        pt: 'Setor de Atividade',
        la: 'Sector Activitatis'
    },
    'jobs.sector_placeholder': {
        en: 'e.g., IT',
        es: 'Ej: Informática',
        fr: 'Ex: Informatique',
        de: 'z.B. IT',
        pt: 'Ex: TI',
        la: 'Exempli gratia: Computatio'
    },
    'jobs.reset_filters': {
        en: 'Reset filters',
        es: 'Restablecer filtros',
        fr: 'Réinitialiser les filtres',
        de: 'Filter zurücksetzen',
        pt: 'Redefinir filtros',
        la: 'Renovare colationes'
    },
    'jobs.offers_found_singular': {
        en: 'offer found',
        es: 'oferta encontrada',
        fr: 'offre trouvée',
        de: 'Angebot gefunden',
        pt: 'oferta encontrada',
        la: 'oblatio inventa'
    },
    'jobs.offers_found_plural': {
        en: 'offers found',
        es: 'ofertas encontradas',
        fr: 'offres trouvées',
        de: 'Angebote gefunden',
        pt: 'ofertas encontradas',
        la: 'oblationes inventae'
    },
    'jobs.loading': {
        en: 'Loading...',
        es: 'Cargando...',
        fr: 'Chargement...',
        de: 'Laden...',
        pt: 'Carregando...',
        la: 'Onerans...'
    },
    'jobs.loading_offers': {
        en: 'Loading offers...',
        es: 'Cargando ofertas...',
        fr: 'Chargement des offres...',
        de: 'Angebote laden...',
        pt: 'Carregando ofertas...',
        la: 'Onerans oblationes...'
    },
    'jobs.error': {
        en: 'Error',
        es: 'Error',
        fr: 'Erreur',
        de: 'Fehler',
        pt: 'Erro',
        la: 'Error'
    },
    'jobs.no_offers_found': {
        en: 'No offers found',
        es: 'No se encontraron ofertas',
        fr: 'Aucune offre trouvée',
        de: 'Keine Angebote gefunden',
        pt: 'Nenhuma oferta encontrada',
        la: 'Nullae oblationes inventae'
    },
    'jobs.untitled': {
        en: 'Untitled',
        es: 'Sin título',
        fr: 'Sans titre',
        de: 'Ohne Titel',
        pt: 'Sem título',
        la: 'Sine titulo'
    },
    'jobs.company_not_specified': {
        en: 'Company not specified',
        es: 'Empresa no especificada',
        fr: 'Entreprise non spécifiée',
        de: 'Unternehmen nicht angegeben',
        pt: 'Empresa não especificada',
        la: 'Societas non specificata'
    },
    'jobs.view_details': {
        en: 'View details',
        es: 'Ver detalles',
        fr: 'Voir les détails',
        de: 'Details anzeigen',
        pt: 'Ver detalhes',
        la: 'Videre particulas'
    },
    // Privacy Policy
    'privacy.title': {
        en: 'Privacy Policy',
        es: 'Política de Privacidad',
        fr: 'Politique de Confidentialité',
        de: 'Datenschutzrichtlinie',
        pt: 'Política de Privacidade',
        la: 'Politica Privatitatis'
    },
    'privacy.last_updated': {
        en: 'Last updated',
        es: 'Última actualización',
        fr: 'Dernière mise à jour',
        de: 'Zuletzt aktualisiert',
        pt: 'Última atualização',
        la: 'Ultima renovatio'
    },
    'privacy.date': {
        en: 'November 25, 2025',
        es: '25 de noviembre de 2025',
        fr: '25 novembre 2025',
        de: '25. November 2025',
        pt: '25 de novembro de 2025',
        la: 'XXV Novembris MMXXV'
    },
    'privacy.intro_title': {
        en: 'Introduction',
        es: 'Introducción',
        fr: 'Introduction',
        de: 'Einführung',
        pt: 'Introdução',
        la: 'Introductio'
    },
    'privacy.intro_text': {
        en: 'This Privacy Policy describes how Dux collects, uses, and protects your personal information when you use our application.',
        es: 'Esta Política de Privacidad describe cómo Dux recopila, utiliza y protege su información personal cuando utiliza nuestra aplicación.',
        fr: 'Cette Politique de Confidentialité décrit comment Dux collecte, utilise et protège vos informations personnelles lorsque vous utilisez notre application.',
        de: 'Diese Datenschutzrichtlinie beschreibt, wie Dux Ihre persönlichen Informationen sammelt, verwendet und schützt, wenn Sie unsere Anwendung nutzen.',
        pt: 'Esta Política de Privacidade descreve como a Dux coleta, usa e protege suas informações pessoais quando você usa nosso aplicativo.',
        la: 'Haec Politica Privatitatis describit quomodo Dux colligit, utitur, et tuetur informationes personales tuas cum applicationem nostram uteris.'
    },
    'privacy.data_collected_title': {
        en: 'Information We Collect',
        es: 'Información que Recopilamos',
        fr: 'Informations que Nous Collectons',
        de: 'Von uns gesammelte Informationen',
        pt: 'Informações que Coletamos',
        la: 'Informationes Quas Colligimus'
    },
    'privacy.data_collected_text': {
        en: 'We collect the following types of information:',
        es: 'Recopilamos los siguientes tipos de información:',
        fr: 'Nous collectons les types d\'informations suivants:',
        de: 'Wir sammeln folgende Arten von Informationen:',
        pt: 'Coletamos os seguintes tipos de informação:',
        la: 'Colligimus has species informationum:'
    },
    'privacy.account_info': {
        en: 'Account Information',
        es: 'Información de Cuenta',
        fr: 'Informations de Compte',
        de: 'Kontoinformationen',
        pt: 'Informações da Conta',
        la: 'Informationes Rationis'
    },
    'privacy.account_info_desc': {
        en: 'Username and password (hashed) when you register',
        es: 'Nombre de usuario y contraseña (hash) cuando te registras',
        fr: 'Nom d\'utilisateur et mot de passe (hashé) lors de votre inscription',
        de: 'Benutzername und Passwort (gehasht) bei der Registrierung',
        pt: 'Nome de usuário e senha (hash) quando você se registra',
        la: 'Nomen usoris et tessera (confusa) cum inscriberis'
    },
    'privacy.profile_info': {
        en: 'Profile Information',
        es: 'Información de Perfil',
        fr: 'Informations de Profil',
        de: 'Profilinformationen',
        pt: 'Informações do Perfil',
        la: 'Informationes Profili'
    },
    'privacy.profile_info_desc': {
        en: 'First name, last name, profile picture, and job title (if provided via LinkedIn)',
        es: 'Nombre, apellido, foto de perfil y título profesional (si se proporciona a través de LinkedIn)',
        fr: 'Prénom, nom, photo de profil et titre professionnel (si fourni via LinkedIn)',
        de: 'Vorname, Nachname, Profilbild und Berufsbezeichnung (falls über LinkedIn bereitgestellt)',
        pt: 'Nome, sobrenome, foto de perfil e cargo (se fornecido via LinkedIn)',
        la: 'Praenomen, cognomen, imago profili, et titulus officii (si per LinkedIn praebetur)'
    },
    'privacy.auth_info': {
        en: 'Authentication Data',
        es: 'Datos de Autenticación',
        fr: 'Données d\'Authentification',
        de: 'Authentifizierungsdaten',
        pt: 'Dados de Autenticação',
        la: 'Data Authentificationis'
    },
    'privacy.auth_info_desc': {
        en: 'Passkey credentials and LinkedIn OAuth tokens',
        es: 'Credenciales de passkey y tokens OAuth de LinkedIn',
        fr: 'Identifiants Passkey et jetons OAuth LinkedIn',
        de: 'Passkey-Anmeldedaten und LinkedIn OAuth-Token',
        pt: 'Credenciais de passkey e tokens OAuth do LinkedIn',
        la: 'Credentiales clavis et tessellae OAuth LinkedIn'
    },
    'privacy.usage_info': {
        en: 'Usage Information',
        es: 'Información de Uso',
        fr: 'Informations d\'Utilisation',
        de: 'Nutzungsinformationen',
        pt: 'Informações de Uso',
        la: 'Informationes Usus'
    },
    'privacy.usage_info_desc': {
        en: 'Login attempts, IP addresses, and session data',
        es: 'Intentos de inicio de sesión, direcciones IP y datos de sesión',
        fr: 'Tentatives de connexion, adresses IP et données de session',
        de: 'Anmeldeversuche, IP-Adressen und Sitzungsdaten',
        pt: 'Tentativas de login, endereços IP e dados de sessão',
        la: 'Conatus intrandi, inscriptiones IP, et data sessionis'
    },
    'privacy.how_we_use_title': {
        en: 'How We Use Your Information',
        es: 'Cómo Utilizamos su Información',
        fr: 'Comment Nous Utilisons Vos Informations',
        de: 'Wie Wir Ihre Informationen Verwenden',
        pt: 'Como Usamos Suas Informações',
        la: 'Quomodo Informationes Tuas Utimur'
    },
    'privacy.how_we_use_text': {
        en: 'We use your information to:',
        es: 'Utilizamos su información para:',
        fr: 'Nous utilisons vos informations pour:',
        de: 'Wir verwenden Ihre Informationen, um:',
        pt: 'Usamos suas informações para:',
        la: 'Informationes tuas utimur ad:'
    },
    'privacy.use_1': {
        en: 'Provide and maintain our service',
        es: 'Proporcionar y mantener nuestro servicio',
        fr: 'Fournir et maintenir notre service',
        de: 'Unseren Service bereitzustellen und aufrechtzuerhalten',
        pt: 'Fornecer e manter nosso serviço',
        la: 'Servitium nostrum praebere et servare'
    },
    'privacy.use_2': {
        en: 'Authenticate and secure your account',
        es: 'Autenticar y proteger su cuenta',
        fr: 'Authentifier et sécuriser votre compte',
        de: 'Ihr Konto zu authentifizieren und zu sichern',
        pt: 'Autenticar e proteger sua conta',
        la: 'Rationem tuam authentificare et tueri'
    },
    'privacy.use_3': {
        en: 'Prevent fraud and unauthorized access',
        es: 'Prevenir fraude y acceso no autorizado',
        fr: 'Prévenir la fraude et les accès non autorisés',
        de: 'Betrug und unbefugten Zugriff zu verhindern',
        pt: 'Prevenir fraudes e acesso não autorizado',
        la: 'Fraudem et aditum non auctoratum impedire'
    },
    'privacy.use_4': {
        en: 'Improve our application and user experience',
        es: 'Mejorar nuestra aplicación y experiencia de usuario',
        fr: 'Améliorer notre application et l\'expérience utilisateur',
        de: 'Unsere Anwendung und Benutzererfahrung zu verbessern',
        pt: 'Melhorar nosso aplicativo e experiência do usuário',
        la: 'Applicationem nostram et experientiam usoris emendare'
    },
    'privacy.linkedin_title': {
        en: 'LinkedIn Integration',
        es: 'Integración con LinkedIn',
        fr: 'Intégration LinkedIn',
        de: 'LinkedIn-Integration',
        pt: 'Integração com LinkedIn',
        la: 'Integratio LinkedIn'
    },
    'privacy.linkedin_text': {
        en: 'When you sign in with LinkedIn, we:',
        es: 'Cuando inicias sesión con LinkedIn, nosotros:',
        fr: 'Lorsque vous vous connectez avec LinkedIn, nous:',
        de: 'Wenn Sie sich mit LinkedIn anmelden:',
        pt: 'Quando você entra com LinkedIn, nós:',
        la: 'Cum LinkedIn intrare vis, nos:'
    },
    'privacy.linkedin_1': {
        en: 'Receive your basic profile information (name, profile picture, LinkedIn ID)',
        es: 'Recibimos su información básica de perfil (nombre, foto de perfil, ID de LinkedIn)',
        fr: 'Recevons vos informations de profil de base (nom, photo de profil, ID LinkedIn)',
        de: 'Erhalten Ihre grundlegenden Profilinformationen (Name, Profilbild, LinkedIn-ID)',
        pt: 'Recebemos suas informações básicas de perfil (nome, foto de perfil, ID do LinkedIn)',
        la: 'Informationes profili tui basilares accipimus (nomen, imago profili, ID LinkedIn)'
    },
    'privacy.linkedin_2': {
        en: 'Store your LinkedIn ID to link your account',
        es: 'Almacenamos su ID de LinkedIn para vincular su cuenta',
        fr: 'Stockons votre ID LinkedIn pour lier votre compte',
        de: 'Speichern Ihre LinkedIn-ID, um Ihr Konto zu verknüpfen',
        pt: 'Armazenamos seu ID do LinkedIn para vincular sua conta',
        la: 'ID LinkedIn tuum servamus ut rationem tuam conectamus'
    },
    'privacy.linkedin_3': {
        en: 'Do not store your LinkedIn password or access token permanently',
        es: 'No almacenamos su contraseña de LinkedIn ni el token de acceso de forma permanente',
        fr: 'Ne stockons pas votre mot de passe LinkedIn ou jeton d\'accès de manière permanente',
        de: 'Speichern Ihr LinkedIn-Passwort oder Zugriffstoken nicht dauerhaft',
        pt: 'Não armazenamos sua senha do LinkedIn ou token de acesso permanentemente',
        la: 'Tesseram tuam LinkedIn aut tessellam aditus permanenter non servamus'
    },
    'privacy.linkedin_policy': {
        en: 'LinkedIn\'s use of your information is governed by LinkedIn\'s Privacy Policy.',
        es: 'El uso de su información por parte de LinkedIn se rige por la Política de Privacidad de LinkedIn.',
        fr: 'L\'utilisation de vos informations par LinkedIn est régie par la Politique de Confidentialité de LinkedIn.',
        de: 'Die Nutzung Ihrer Informationen durch LinkedIn unterliegt der Datenschutzrichtlinie von LinkedIn.',
        pt: 'O uso de suas informações pelo LinkedIn é regido pela Política de Privacidade do LinkedIn.',
        la: 'Usus informationum tuarum a LinkedIn regitur Politica Privatitatis LinkedIn.'
    },
    'privacy.data_security_title': {
        en: 'Data Security',
        es: 'Seguridad de Datos',
        fr: 'Sécurité des Données',
        de: 'Datensicherheit',
        pt: 'Segurança de Dados',
        la: 'Securitas Datorum'
    },
    'privacy.data_security_text': {
        en: 'We implement industry-standard security measures including password hashing (Argon2), secure session management, rate limiting, and HTTPS encryption to protect your data.',
        es: 'Implementamos medidas de seguridad estándar de la industria, incluyendo hash de contraseñas (Argon2), gestión segura de sesiones, limitación de tasa y cifrado HTTPS para proteger sus datos.',
        fr: 'Nous mettons en œuvre des mesures de sécurité standard de l\'industrie, y compris le hachage de mot de passe (Argon2), la gestion sécurisée des sessions, la limitation de débit et le cryptage HTTPS pour protéger vos données.',
        de: 'Wir implementieren branchenübliche Sicherheitsmaßnahmen, einschließlich Passwort-Hashing (Argon2), sichere Sitzungsverwaltung, Ratenbegrenzung und HTTPS-Verschlüsselung zum Schutz Ihrer Daten.',
        pt: 'Implementamos medidas de segurança padrão da indústria, incluindo hash de senha (Argon2), gerenciamento seguro de sessão, limitação de taxa e criptografia HTTPS para proteger seus dados.',
        la: 'Mensuras securitatis industriae normales implemus includentes confusionem tesserae (Argon2), administrationem sessionis tutam, limitationem tariffae, et encryptionem HTTPS ad data tua protegenda.'
    },
    'privacy.data_retention_title': {
        en: 'Data Retention',
        es: 'Retención de Datos',
        fr: 'Conservation des Données',
        de: 'Datenspeicherung',
        pt: 'Retenção de Dados',
        la: 'Retentio Datorum'
    },
    'privacy.data_retention_text': {
        en: 'We retain your account information for as long as your account is active. Login attempts and session data are retained for security purposes for a limited time.',
        es: 'Conservamos la información de su cuenta mientras su cuenta esté activa. Los intentos de inicio de sesión y los datos de sesión se conservan con fines de seguridad durante un tiempo limitado.',
        fr: 'Nous conservons les informations de votre compte tant que votre compte est actif. Les tentatives de connexion et les données de session sont conservées à des fins de sécurité pendant une durée limitée.',
        de: 'Wir speichern Ihre Kontoinformationen, solange Ihr Konto aktiv ist. Anmeldeversuche und Sitzungsdaten werden zu Sicherheitszwecken für eine begrenzte Zeit gespeichert.',
        pt: 'Retemos as informações da sua conta enquanto sua conta estiver ativa. Tentativas de login e dados de sessão são retidos para fins de segurança por um tempo limitado.',
        la: 'Informationes rationis tuae retinemus quamdiu ratio tua activa est. Conatus intrandi et data sessionis ad fines securitatis tempore limitato retinemus.'
    },
    'privacy.your_rights_title': {
        en: 'Your Rights',
        es: 'Sus Derechos',
        fr: 'Vos Droits',
        de: 'Ihre Rechte',
        pt: 'Seus Direitos',
        la: 'Iura Tua'
    },
    'privacy.your_rights_text': {
        en: 'You have the right to:',
        es: 'Usted tiene derecho a:',
        fr: 'Vous avez le droit de:',
        de: 'Sie haben das Recht:',
        pt: 'Você tem o direito de:',
        la: 'Ius habes ad:'
    },
    'privacy.right_access': {
        en: 'Access your data',
        es: 'Acceder a sus datos',
        fr: 'Accéder à vos données',
        de: 'Zugriff auf Ihre Daten',
        pt: 'Acessar seus dados',
        la: 'Data tua adire'
    },
    'privacy.right_access_desc': {
        en: 'View your account information at any time',
        es: 'Ver la información de su cuenta en cualquier momento',
        fr: 'Consulter les informations de votre compte à tout moment',
        de: 'Ihre Kontoinformationen jederzeit einsehen',
        pt: 'Visualizar as informações da sua conta a qualquer momento',
        la: 'Informationes rationis tuae quovis tempore videre'
    },
    'privacy.right_deletion': {
        en: 'Request deletion',
        es: 'Solicitar eliminación',
        fr: 'Demander la suppression',
        de: 'Löschung beantragen',
        pt: 'Solicitar exclusão',
        la: 'Deletionem petere'
    },
    'privacy.right_deletion_desc': {
        en: 'Delete your account and associated data',
        es: 'Eliminar su cuenta y los datos asociados',
        fr: 'Supprimer votre compte et les données associées',
        de: 'Ihr Konto und zugehörige Daten löschen',
        pt: 'Excluir sua conta e dados associados',
        la: 'Rationem tuam et data consociata delere'
    },
    'privacy.right_correction': {
        en: 'Correct your data',
        es: 'Corregir sus datos',
        fr: 'Corriger vos données',
        de: 'Ihre Daten korrigieren',
        pt: 'Corrigir seus dados',
        la: 'Data tua corrigere'
    },
    'privacy.right_correction_desc': {
        en: 'Update or modify your profile information',
        es: 'Actualizar o modificar la información de su perfil',
        fr: 'Mettre à jour ou modifier les informations de votre profil',
        de: 'Ihre Profilinformationen aktualisieren oder ändern',
        pt: 'Atualizar ou modificar as informações do seu perfil',
        la: 'Informationes profili tui renovare aut modificare'
    },
    'privacy.cookies_title': {
        en: 'Cookies and Session Management',
        es: 'Cookies y Gestión de Sesiones',
        fr: 'Cookies et Gestion des Sessions',
        de: 'Cookies und Sitzungsverwaltung',
        pt: 'Cookies e Gerenciamento de Sessão',
        la: 'Crustula et Administratio Sessionis'
    },
    'privacy.cookies_text': {
        en: 'We use secure session cookies to maintain your login state. These cookies are essential for the application to function and are deleted when you log out.',
        es: 'Utilizamos cookies de sesión seguras para mantener su estado de inicio de sesión. Estas cookies son esenciales para que la aplicación funcione y se eliminan cuando cierra sesión.',
        fr: 'Nous utilisons des cookies de session sécurisés pour maintenir votre état de connexion. Ces cookies sont essentiels au fonctionnement de l\'application et sont supprimés lorsque vous vous déconnectez.',
        de: 'Wir verwenden sichere Sitzungs-Cookies, um Ihren Anmeldestatus aufrechtzuerhalten. Diese Cookies sind für die Funktion der Anwendung unerlässlich und werden gelöscht, wenn Sie sich abmelden.',
        pt: 'Usamos cookies de sessão seguros para manter seu estado de login. Esses cookies são essenciais para o funcionamento do aplicativo e são excluídos quando você faz logout.',
        la: 'Crustula sessionis tuta utimur ad statum intrandi tuum servandum. Haec crustula essentiales sunt ad applicationem functuram et delentur cum exieris.'
    },
    'privacy.third_party_title': {
        en: 'Third-Party Services',
        es: 'Servicios de Terceros',
        fr: 'Services Tiers',
        de: 'Dienste Dritter',
        pt: 'Serviços de Terceiros',
        la: 'Servitia Tertiae Partis'
    },
    'privacy.third_party_text': {
        en: 'We integrate with LinkedIn for authentication purposes. LinkedIn may collect and process data according to their own privacy policy.',
        es: 'Nos integramos con LinkedIn con fines de autenticación. LinkedIn puede recopilar y procesar datos según su propia política de privacidad.',
        fr: 'Nous nous intégrons à LinkedIn à des fins d\'authentification. LinkedIn peut collecter et traiter des données selon sa propre politique de confidentialité.',
        de: 'Wir integrieren LinkedIn zu Authentifizierungszwecken. LinkedIn kann Daten gemäß ihrer eigenen Datenschutzrichtlinie sammeln und verarbeiten.',
        pt: 'Integramos com o LinkedIn para fins de autenticação. O LinkedIn pode coletar e processar dados de acordo com sua própria política de privacidade.',
        la: 'Cum LinkedIn ad fines authentificationis integramus. LinkedIn data colligere et tractare potest secundum suam politicam privatitatis.'
    },
    'privacy.changes_title': {
        en: 'Changes to This Policy',
        es: 'Cambios a Esta Política',
        fr: 'Modifications de Cette Politique',
        de: 'Änderungen dieser Richtlinie',
        pt: 'Alterações a Esta Política',
        la: 'Mutationes Huius Politicae'
    },
    'privacy.changes_text': {
        en: 'We may update this Privacy Policy from time to time. We will notify you of any changes by updating the "Last updated" date.',
        es: 'Podemos actualizar esta Política de Privacidad de vez en cuando. Le notificaremos de cualquier cambio actualizando la fecha de "Última actualización".',
        fr: 'Nous pouvons mettre à jour cette Politique de Confidentialité de temps en temps. Nous vous informerons de tout changement en mettant à jour la date "Dernière mise à jour".',
        de: 'Wir können diese Datenschutzrichtlinie von Zeit zu Zeit aktualisieren. Wir werden Sie über Änderungen informieren, indem wir das Datum "Zuletzt aktualisiert" aktualisieren.',
        pt: 'Podemos atualizar esta Política de Privacidade de tempos em tempos. Notificaremos você sobre quaisquer alterações atualizando a data "Última atualização".',
        la: 'Hanc Politicam Privatitatis interdum renovare possumus. Te de mutationibus certiorem faciemus renovando datam "Ultima renovatio".'
    },
    'privacy.contact_title': {
        en: 'Contact Us',
        es: 'Contáctenos',
        fr: 'Nous Contacter',
        de: 'Kontaktieren Sie Uns',
        pt: 'Entre em Contato',
        la: 'Nos Contacta'
    },
    'privacy.contact_text': {
        en: 'If you have any questions about this Privacy Policy, please contact us through your account settings.',
        es: 'Si tiene alguna pregunta sobre esta Política de Privacidad, contáctenos a través de la configuración de su cuenta.',
        fr: 'Si vous avez des questions concernant cette Politique de Confidentialité, veuillez nous contacter via les paramètres de votre compte.',
        de: 'Wenn Sie Fragen zu dieser Datenschutzrichtlinie haben, kontaktieren Sie uns bitte über Ihre Kontoeinstellungen.',
        pt: 'Se você tiver alguma dúvida sobre esta Política de Privacidade, entre em contato conosco através das configurações da sua conta.',
        la: 'Si quaestiones de hac Politica Privatitatis habes, nos contacta per configurationes rationis tuae.'
    },
    'privacy.by_using': {
        en: 'By using this service, you agree to our',
        es: 'Al usar este servicio, acepta nuestra',
        fr: 'En utilisant ce service, vous acceptez notre',
        de: 'Durch die Nutzung dieses Dienstes stimmen Sie unserer',
        pt: 'Ao usar este serviço, você concorda com nossa',
        la: 'Hoc servitio utendo, nostram consentis'
    },
    // Profile Setup
    'setup.title': {
        en: 'Complete Your Profile',
        es: 'Completa Tu Perfil',
        fr: 'Complétez Votre Profil',
        de: 'Vervollständigen Sie Ihr Profil',
        pt: 'Complete Seu Perfil',
        la: 'Professionem Tuam Comple'
    },
    'setup.description': {
        en: 'Help us understand your background better by completing your profile.',
        es: 'Ayúdanos a entender mejor tu experiencia completando tu perfil.',
        fr: 'Aidez-nous à mieux comprendre votre parcours en complétant votre profil.',
        de: 'Helfen Sie uns, Ihren Hintergrund besser zu verstehen, indem Sie Ihr Profil vervollständigen.',
        pt: 'Ajude-nos a entender melhor seu histórico completando seu perfil.',
        la: 'Adiuva nos melius intellegere historiam tuam perficiendo professionem tuam.'
    },
    'setup.cv_upload': {
        en: 'Upload Your CV',
        es: 'Sube Tu CV',
        fr: 'Téléchargez Votre CV',
        de: 'Laden Sie Ihren Lebenslauf Hoch',
        pt: 'Envie Seu Currículo',
        la: 'Curriculum Vitae Tuum Transfere'
    },
    'setup.upload_cv': {
        en: 'Upload CV',
        es: 'Subir CV',
        fr: 'Télécharger le CV',
        de: 'Lebenslauf Hochladen',
        pt: 'Enviar Currículo',
        la: 'Transfere CV'
    },
    'setup.skip_cv': {
        en: 'Skip for Now',
        es: 'Omitir por Ahora',
        fr: 'Passer pour le Moment',
        de: 'Jetzt Überspringen',
        pt: 'Pular por Enquanto',
        la: 'Praeterire Nunc'
    },
    'setup.profile_info': {
        en: 'Profile Information',
        es: 'Información del Perfil',
        fr: 'Informations de Profil',
        de: 'Profilinformationen',
        pt: 'Informações do Perfil',
        la: 'Informationes Professionis'
    },
    'setup.headline': {
        en: 'Professional Headline',
        es: 'Título Profesional',
        fr: 'Titre Professionnel',
        de: 'Berufsbezeichnung',
        pt: 'Título Profissional',
        la: 'Titulus Professionalis'
    },
    'setup.location': {
        en: 'Location',
        es: 'Ubicación',
        fr: 'Emplacement',
        de: 'Standort',
        pt: 'Localização',
        la: 'Locus'
    },
    'setup.summary': {
        en: 'Professional Summary',
        es: 'Resumen Profesional',
        fr: 'Résumé Professionnel',
        de: 'Berufliche Zusammenfassung',
        pt: 'Resumo Profissional',
        la: 'Summarium Professionale'
    },
    'setup.summary_placeholder': {
        en: 'Tell us about your professional background and goals...',
        es: 'Cuéntanos sobre tu experiencia profesional y objetivos...',
        fr: 'Parlez-nous de votre parcours professionnel et de vos objectifs...',
        de: 'Erzählen Sie uns von Ihrem beruflichen Hintergrund und Ihren Zielen...',
        pt: 'Conte-nos sobre sua experiência profissional e objetivos...',
        la: 'Nobis narra de historia tua professionali et scopos...'
    },
    'setup.skills': {
        en: 'Skills',
        es: 'Habilidades',
        fr: 'Compétences',
        de: 'Fähigkeiten',
        pt: 'Habilidades',
        la: 'Artes'
    },
    'setup.add_skill': {
        en: 'Add',
        es: 'Añadir',
        fr: 'Ajouter',
        de: 'Hinzufügen',
        pt: 'Adicionar',
        la: 'Addere'
    },
    'setup.experience': {
        en: 'Work Experience',
        es: 'Experiencia Laboral',
        fr: 'Expérience Professionnelle',
        de: 'Berufserfahrung',
        pt: 'Experiência Profissional',
        la: 'Experientia Laboris'
    },
    'setup.company': {
        en: 'Company',
        es: 'Empresa',
        fr: 'Entreprise',
        de: 'Unternehmen',
        pt: 'Empresa',
        la: 'Societas'
    },
    'setup.job_title': {
        en: 'Job Title',
        es: 'Puesto',
        fr: 'Poste',
        de: 'Berufsbezeichnung',
        pt: 'Cargo',
        la: 'Titulus Officii'
    },
    'setup.start_date': {
        en: 'Start Date',
        es: 'Fecha de Inicio',
        fr: 'Date de Début',
        de: 'Startdatum',
        pt: 'Data de Início',
        la: 'Dies Initii'
    },
    'setup.end_date': {
        en: 'End Date',
        es: 'Fecha de Fin',
        fr: 'Date de Fin',
        de: 'Enddatum',
        pt: 'Data de Término',
        la: 'Dies Finis'
    },
    'setup.current_position': {
        en: 'I currently work here',
        es: 'Actualmente trabajo aquí',
        fr: 'Je travaille actuellement ici',
        de: 'Ich arbeite derzeit hier',
        pt: 'Atualmente trabalho aqui',
        la: 'Nunc hic laboro'
    },
    'setup.job_description': {
        en: 'Job Description',
        es: 'Descripción del Trabajo',
        fr: 'Description du Poste',
        de: 'Stellenbeschreibung',
        pt: 'Descrição do Cargo',
        la: 'Descriptio Officii'
    },
    'setup.add_experience': {
        en: 'Add Another Experience',
        es: 'Añadir Otra Experiencia',
        fr: 'Ajouter une Autre Expérience',
        de: 'Weitere Erfahrung Hinzufügen',
        pt: 'Adicionar Outra Experiência',
        la: 'Addere Aliam Experientiam'
    },
    'setup.remove': {
        en: 'Remove',
        es: 'Eliminar',
        fr: 'Supprimer',
        de: 'Entfernen',
        pt: 'Remover',
        la: 'Removere'
    },
    'setup.education': {
        en: 'Education',
        es: 'Educación',
        fr: 'Éducation',
        de: 'Bildung',
        pt: 'Educação',
        la: 'Educatio'
    },
    'setup.school': {
        en: 'School',
        es: 'Escuela',
        fr: 'École',
        de: 'Schule',
        pt: 'Escola',
        la: 'Schola'
    },
    'setup.degree': {
        en: 'Degree',
        es: 'Título',
        fr: 'Diplôme',
        de: 'Abschluss',
        pt: 'Grau',
        la: 'Gradus'
    },
    'setup.field_of_study': {
        en: 'Field of Study',
        es: 'Campo de Estudio',
        fr: 'Domaine d\'Étude',
        de: 'Studienfach',
        pt: 'Área de Estudo',
        la: 'Campus Studii'
    },
    'setup.education_description': {
        en: 'Description',
        es: 'Descripción',
        fr: 'Description',
        de: 'Beschreibung',
        pt: 'Descrição',
        la: 'Descriptio'
    },
    'setup.add_education': {
        en: 'Add Another Education',
        es: 'Añadir Otra Educación',
        fr: 'Ajouter une Autre Formation',
        de: 'Weitere Ausbildung Hinzufügen',
        pt: 'Adicionar Outra Educação',
        la: 'Addere Aliam Educationem'
    },
    'setup.next': {
        en: 'Next',
        es: 'Siguiente',
        fr: 'Suivant',
        de: 'Weiter',
        pt: 'Próximo',
        la: 'Sequens'
    },
    'setup.back': {
        en: 'Back',
        es: 'Atrás',
        fr: 'Retour',
        de: 'Zurück',
        pt: 'Voltar',
        la: 'Redire'
    },
    'setup.complete': {
        en: 'Complete Setup',
        es: 'Completar Configuración',
        fr: 'Terminer la Configuration',
        de: 'Einrichtung Abschließen',
        pt: 'Concluir Configuração',
        la: 'Perficere Configurationem'
    },
    'setup.saving': {
        en: 'Saving...',
        es: 'Guardando...',
        fr: 'Enregistrement...',
        de: 'Speichern...',
        pt: 'Salvando...',
        la: 'Servans...'
    },
    'setup.skip_for_now': {
        en: 'Skip and Complete Later',
        es: 'Omitir y Completar Después',
        fr: 'Passer et Compléter Plus Tard',
        de: 'Überspringen und Später Abschließen',
        pt: 'Pular e Completar Depois',
        la: 'Praeterire et Postea Perficere'
    },
    // Account Settings
    'settings.auth_methods': {
        en: 'Authentication Methods',
        es: 'Métodos de Autenticación',
        fr: 'Méthodes d\'Authentification',
        de: 'Authentifizierungsmethoden',
        pt: 'Métodos de Autenticação',
        la: 'Methodi Authentificationis'
    },
    'settings.auth_methods_desc': {
        en: 'Add multiple authentication methods to your account for easier access.',
        es: 'Agregue múltiples métodos de autenticación a su cuenta para facilitar el acceso.',
        fr: 'Ajoutez plusieurs méthodes d\'authentification à votre compte pour un accès plus facile.',
        de: 'Fügen Sie mehrere Authentifizierungsmethoden zu Ihrem Konto hinzu, um den Zugriff zu erleichtern.',
        pt: 'Adicione vários métodos de autenticação à sua conta para facilitar o acesso.',
        la: 'Methodos authentificationis plures rationi tuae adde ad aditum faciliorem.'
    },
    'settings.configured': {
        en: 'Configured',
        es: 'Configurado',
        fr: 'Configuré',
        de: 'Konfiguriert',
        pt: 'Configurado',
        la: 'Configuratum'
    },
    'settings.not_configured': {
        en: 'Not configured',
        es: 'No configurado',
        fr: 'Non configuré',
        de: 'Nicht konfiguriert',
        pt: 'Não configurado',
        la: 'Non configuratum'
    },
    'settings.password_note': {
        en: 'Set at registration',
        es: 'Establecido en el registro',
        fr: 'Défini lors de l\'inscription',
        de: 'Bei der Registrierung festgelegt',
        pt: 'Definido no registro',
        la: 'Positum in inscriptione'
    },
    'settings.add_passkey': {
        en: 'Add Passkey',
        es: 'Agregar Passkey',
        fr: 'Ajouter Passkey',
        de: 'Passkey Hinzufügen',
        pt: 'Adicionar Passkey',
        la: 'Addere Clavem'
    },
    'settings.link_linkedin': {
        en: 'Link LinkedIn',
        es: 'Vincular LinkedIn',
        fr: 'Lier LinkedIn',
        de: 'LinkedIn Verknüpfen',
        pt: 'Vincular LinkedIn',
        la: 'Conectere LinkedIn'
    },
    'settings.passkey_added': {
        en: 'Passkey added successfully!',
        es: '¡Passkey agregado exitosamente!',
        fr: 'Passkey ajouté avec succès!',
        de: 'Passkey erfolgreich hinzugefügt!',
        pt: 'Passkey adicionado com sucesso!',
        la: 'Clavis feliciter addita!'
    },
    'settings.passkey_add_failed': {
        en: 'Failed to add passkey',
        es: 'Error al agregar passkey',
        fr: 'Échec de l\'ajout de passkey',
        de: 'Passkey konnte nicht hinzugefügt werden',
        pt: 'Falha ao adicionar passkey',
        la: 'Clavem addere defecit'
    },
    'settings.linkedin_linked': {
        en: 'LinkedIn linked successfully!',
        es: '¡LinkedIn vinculado exitosamente!',
        fr: 'LinkedIn lié avec succès!',
        de: 'LinkedIn erfolgreich verknüpft!',
        pt: 'LinkedIn vinculado com sucesso!',
        la: 'LinkedIn feliciter conectum!'
    },
    'settings.linkedin_link_failed': {
        en: 'Failed to link LinkedIn',
        es: 'Error al vincular LinkedIn',
        fr: 'Échec de la liaison LinkedIn',
        de: 'LinkedIn konnte nicht verknüpft werden',
        pt: 'Falha ao vincular LinkedIn',
        la: 'LinkedIn conectere defecit'
    },
    'settings.setup_password': {
        en: 'Setup Password',
        es: 'Configurar Contraseña',
        fr: 'Configurer le Mot de Passe',
        de: 'Passwort Einrichten',
        pt: 'Configurar Senha',
        la: 'Configurare Tesseram'
    },
    'settings.password_requirements': {
        en: 'Password must be at least 12 characters with uppercase, lowercase, number, and special character.',
        es: 'La contraseña debe tener al menos 12 caracteres con mayúsculas, minúsculas, números y caracteres especiales.',
        fr: 'Le mot de passe doit contenir au moins 12 caractères avec majuscules, minuscules, chiffres et caractères spéciaux.',
        de: 'Das Passwort muss mindestens 12 Zeichen mit Groß-, Kleinbuchstaben, Zahlen und Sonderzeichen enthalten.',
        pt: 'A senha deve ter pelo menos 12 caracteres com maiúsculas, minúsculas, números e caracteres especiais.',
        la: 'Tessera minimum XII characteres cum maiusculis, minusculis, numero, et charactere speciali habere debet.'
    },
    'settings.new_password': {
        en: 'New Password',
        es: 'Nueva Contraseña',
        fr: 'Nouveau Mot de Passe',
        de: 'Neues Passwort',
        pt: 'Nova Senha',
        la: 'Tessera Nova'
    },
    'settings.confirm_password': {
        en: 'Confirm Password',
        es: 'Confirmar Contraseña',
        fr: 'Confirmer le Mot de Passe',
        de: 'Passwort Bestätigen',
        pt: 'Confirmar Senha',
        la: 'Tesseram Confirmare'
    },
    'settings.setup': {
        en: 'Setup',
        es: 'Configurar',
        fr: 'Configurer',
        de: 'Einrichten',
        pt: 'Configurar',
        la: 'Configurare'
    },
    'settings.setting_up': {
        en: 'Setting up...',
        es: 'Configurando...',
        fr: 'Configuration...',
        de: 'Einrichten...',
        pt: 'Configurando...',
        la: 'Configurando...'
    },
    'settings.cancel': {
        en: 'Cancel',
        es: 'Cancelar',
        fr: 'Annuler',
        de: 'Abbrechen',
        pt: 'Cancelar',
        la: 'Revocare'
    },
    'settings.password_set': {
        en: 'Password set successfully!',
        es: '¡Contraseña configurada exitosamente!',
        fr: 'Mot de passe configuré avec succès!',
        de: 'Passwort erfolgreich eingerichtet!',
        pt: 'Senha configurada com sucesso!',
        la: 'Tessera feliciter posita!'
    },
    'settings.password_set_failed': {
        en: 'Failed to set password',
        es: 'Error al configurar contraseña',
        fr: 'Échec de la configuration du mot de passe',
        de: 'Passwort konnte nicht eingerichtet werden',
        pt: 'Falha ao configurar senha',
        la: 'Tesseram ponere defecit'
    },
    'settings.passwords_dont_match': {
        en: 'Passwords do not match',
        es: 'Las contraseñas no coinciden',
        fr: 'Les mots de passe ne correspondent pas',
        de: 'Passwörter stimmen nicht überein',
        pt: 'As senhas não coincidem',
        la: 'Tesserae non concordant'
    },
    'settings.password_too_short': {
        en: 'Password must be at least 12 characters',
        es: 'La contraseña debe tener al menos 12 caracteres',
        fr: 'Le mot de passe doit contenir au moins 12 caractères',
        de: 'Das Passwort muss mindestens 12 Zeichen enthalten',
        pt: 'A senha deve ter pelo menos 12 caracteres',
        la: 'Tessera minimum XII characteres habere debet'
    },
    'preferences.title': {
        en: 'Preferences',
        es: 'Preferencias',
        fr: 'Préférences',
        de: 'Einstellungen',
        pt: 'Preferências',
        la: 'Praeferentiae'
    },
    'preferences.language': {
        en: 'Language',
        es: 'Idioma',
        fr: 'Langue',
        de: 'Sprache',
        pt: 'Idioma',
        la: 'Lingua'
    },
    'preferences.theme': {
        en: 'Theme',
        es: 'Tema',
        fr: 'Thème',
        de: 'Theme',
        pt: 'Tema',
        la: 'Thema'
    },
    'preferences.danger_zone': {
        en: 'Danger Zone',
        es: 'Zona de Peligro',
        fr: 'Zone Dangereuse',
        de: 'Gefahrenzone',
        pt: 'Zona de Perigo',
        la: 'Zona Periculi'
    },
    'preferences.delete_warning': {
        en: 'Once you delete your account, there is no going back. Please be certain.',
        es: 'Una vez que elimines tu cuenta, no hay vuelta atrás. Por favor, asegúrate.',
        fr: 'Une fois votre compte supprimé, il n\'y a pas de retour en arrière. Soyez certain.',
        de: 'Sobald Sie Ihr Konto löschen, gibt es kein Zurück. Bitte seien Sie sicher.',
        pt: 'Uma vez que você excluir sua conta, não há volta. Por favor, tenha certeza.',
        la: 'Semel rationem tuam deleveris, regressus nullus est. Certus esto.'
    },
    'preferences.delete_account': {
        en: 'Delete Account',
        es: 'Eliminar Cuenta',
        fr: 'Supprimer le Compte',
        de: 'Konto Löschen',
        pt: 'Excluir Conta',
        la: 'Rationem Delere'
    },
    'preferences.confirm_delete': {
        en: 'Are you sure?',
        es: '¿Estás seguro?',
        fr: 'Êtes-vous sûr?',
        de: 'Sind Sie sicher?',
        pt: 'Tem certeza?',
        la: 'Certusne es?'
    },
    'preferences.confirm_delete_message': {
        en: 'This will permanently delete your account and all associated data. This action cannot be undone.',
        es: 'Esto eliminará permanentemente tu cuenta y todos los datos asociados. Esta acción no se puede deshacer.',
        fr: 'Cela supprimera définitivement votre compte et toutes les données associées. Cette action ne peut pas être annulée.',
        de: 'Dadurch werden Ihr Konto und alle zugehörigen Daten dauerhaft gelöscht. Diese Aktion kann nicht rückgängig gemacht werden.',
        pt: 'Isso excluirá permanentemente sua conta e todos os dados associados. Esta ação não pode ser desfeita.',
        la: 'Hoc rationem tuam et omnia data consociata perpetuo delebit. Haec actio revocari non potest.'
    },
    'preferences.delete_permanently': {
        en: 'Delete Permanently',
        es: 'Eliminar Permanentemente',
        fr: 'Supprimer Définitivement',
        de: 'Dauerhaft Löschen',
        pt: 'Excluir Permanentemente',
        la: 'Perpetuo Delere'
    },
    'common.cancel': {
        en: 'Cancel',
        es: 'Cancelar',
        fr: 'Annuler',
        de: 'Abbrechen',
        pt: 'Cancelar',
        la: 'Revocare'
    },
    'common.deleting': {
        en: 'Deleting...',
        es: 'Eliminando...',
        fr: 'Suppression...',
        de: 'Löschen...',
        pt: 'Excluindo...',
        la: 'Delendo...'
    },
    'settings.page_title': {
        en: 'Settings',
        es: 'Configuración',
        fr: 'Paramètres',
        de: 'Einstellungen',
        pt: 'Configurações',
        la: 'Configurationes'
    },
    'settings.page_description': {
        en: 'Manage your account, authentication methods, and preferences.',
        es: 'Administra tu cuenta, métodos de autenticación y preferencias.',
        fr: 'Gérez votre compte, vos méthodes d\'authentification et vos préférences.',
        de: 'Verwalten Sie Ihr Konto, Authentifizierungsmethoden und Einstellungen.',
        pt: 'Gerencie sua conta, métodos de autenticação e preferências.',
        la: 'Rationem tuam, methodos authentificationis, et praeferentias administra.'
    },
    // Common/Error Messages
    'common.popup_blocked': {
        en: 'Popup blocked. Please allow popups.',
        es: 'Ventana emergente bloqueada. Por favor, permite las ventanas emergentes.',
        fr: 'Fenêtre contextuelle bloquée. Veuillez autoriser les fenêtres contextuelles.',
        de: 'Popup blockiert. Bitte erlauben Sie Popups.',
        pt: 'Pop-up bloqueado. Por favor, permita pop-ups.',
        la: 'Fenestra erumpens impedita. Fenestras erumpentes permitte.'
    },
    'common.popup_blocked_site': {
        en: 'Popup blocked. Please allow popups for this site.',
        es: 'Ventana emergente bloqueada. Por favor, permite las ventanas emergentes para este sitio.',
        fr: 'Fenêtre contextuelle bloquée. Veuillez autoriser les fenêtres contextuelles pour ce site.',
        de: 'Popup blockiert. Bitte erlauben Sie Popups für diese Seite.',
        pt: 'Pop-up bloqueado. Por favor, permita pop-ups para este site.',
        la: 'Fenestra erumpens impedita. Fenestras erumpentes pro hoc sito permitte.'
    },
    'common.error': {
        en: 'Error',
        es: 'Error',
        fr: 'Erreur',
        de: 'Fehler',
        pt: 'Erro',
        la: 'Error'
    },
    // Job Offers Card
    'jobs.optimal_offers': {
        en: 'Optimal Offers',
        es: 'Ofertas Óptimas',
        fr: 'Offres Optimales',
        de: 'Optimale Angebote',
        pt: 'Ofertas Ideais',
        la: 'Offerta Optima'
    },
    'jobs.find_offers': {
        en: 'Find Offers',
        es: 'Encontrar Ofertas',
        fr: 'Trouver des Offres',
        de: 'Angebote Finden',
        pt: 'Encontrar Ofertas',
        la: 'Offerta Invenire'
    },
    'jobs.refresh_offers': {
        en: 'Refresh Offers',
        es: 'Actualizar Ofertas',
        fr: 'Actualiser les Offres',
        de: 'Angebote Aktualisieren',
        pt: 'Atualizar Ofertas',
        la: 'Offerta Renovare'
    },
    'jobs.upload_cv_to_match': {
        en: 'Upload a CV and run profile matching to see offers.',
        es: 'Sube un CV y ejecuta el emparejamiento de perfil para ver ofertas.',
        fr: 'Téléchargez un CV et lancez la correspondance de profil pour voir les offres.',
        de: 'Laden Sie einen Lebenslauf hoch und führen Sie das Profil-Matching durch, um Angebote zu sehen.',
        pt: 'Envie um currículo e execute a correspondência de perfil para ver ofertas.',
        la: 'Curriculum mitte et comparationem profili exerce ut offerta videas.'
    },
    'jobs.why_match': {
        en: 'Why Match',
        es: 'Por qué Coincide',
        fr: 'Pourquoi Correspond',
        de: 'Warum Passt',
        pt: 'Por que Corresponde',
        la: 'Cur Congruit'
    },
    'jobs.match_score': {
        en: 'Match Score',
        es: 'Puntuación de Coincidencia',
        fr: 'Score de Correspondance',
        de: 'Übereinstimmungswert',
        pt: 'Pontuação de Correspondência',
        la: 'Punctus Congruentiae'
    },
    'jobs.concerns': {
        en: 'Concerns',
        es: 'Preocupaciones',
        fr: 'Préoccupations',
        de: 'Bedenken',
        pt: 'Preocupações',
        la: 'Sollicitudines'
    },
    // Debug Card
    'debug.title': {
        en: 'Debug Information',
        es: 'Información de Depuración',
        fr: 'Informations de Débogage',
        de: 'Debug-Informationen',
        pt: 'Informações de Depuração',
        la: 'Informationes Emendationis'
    },
    'debug.description': {
        en: 'Detailed user data for debugging',
        es: 'Datos detallados del usuario para depuración',
        fr: 'Données utilisateur détaillées pour le débogage',
        de: 'Detaillierte Benutzerdaten zum Debuggen',
        pt: 'Dados detalhados do usuário para depuração',
        la: 'Data usoris detaliata pro emendatione'
    },
    'debug.refresh': {
        en: 'Refresh',
        es: 'Actualizar',
        fr: 'Actualiser',
        de: 'Aktualisieren',
        pt: 'Atualizar',
        la: 'Renovare'
    },
    'debug.loading': {
        en: 'Loading...',
        es: 'Cargando...',
        fr: 'Chargement...',
        de: 'Laden...',
        pt: 'Carregando...',
        la: 'Onerando...'
    },
    'debug.show_details': {
        en: 'Show Details',
        es: 'Mostrar Detalles',
        fr: 'Afficher les Détails',
        de: 'Details Anzeigen',
        pt: 'Mostrar Detalhes',
        la: 'Detalia Monstrare'
    },
    'debug.hide_details': {
        en: 'Hide Details',
        es: 'Ocultar Detalles',
        fr: 'Masquer les Détails',
        de: 'Details Ausblenden',
        pt: 'Ocultar Detalhes',
        la: 'Detalia Celare'
    },
    'debug.loading_info': {
        en: 'Loading debug information...',
        es: 'Cargando información de depuración...',
        fr: 'Chargement des informations de débogage...',
        de: 'Debug-Informationen werden geladen...',
        pt: 'Carregando informações de depuração...',
        la: 'Informationes emendationis onerando...'
    },
    'debug.test_matching': {
        en: 'Test Profile Matching',
        es: 'Probar Emparejamiento de Perfil',
        fr: 'Tester la Correspondance de Profil',
        de: 'Profil-Matching Testen',
        pt: 'Testar Correspondência de Perfil',
        la: 'Comparationem Profili Probare'
    },
    'debug.query_label': {
        en: 'Query / Preferences',
        es: 'Consulta / Preferencias',
        fr: 'Requête / Préférences',
        de: 'Abfrage / Einstellungen',
        pt: 'Consulta / Preferências',
        la: 'Quaestio / Praeferentiae'
    },
    'debug.query_placeholder': {
        en: 'e.g., I\'m interested in machine learning positions',
        es: 'p. ej., Me interesan las posiciones de aprendizaje automático',
        fr: 'p. ex., Je suis intéressé par les postes en apprentissage automatique',
        de: 'z.B., Ich interessiere mich für Positionen im maschinellen Lernen',
        pt: 'ex., Estou interessado em posições de aprendizado de máquina',
        la: 'e.g., Positiones machinae disciplinae me intersunt'
    },
    'debug.model_label': {
        en: 'Model (optional)',
        es: 'Modelo (opcional)',
        fr: 'Modèle (facultatif)',
        de: 'Modell (optional)',
        pt: 'Modelo (opcional)',
        la: 'Exemplar (optionale)'
    },
    'debug.model_placeholder': {
        en: 'e.g., gpt-4 (leave empty for default)',
        es: 'p. ej., gpt-4 (dejar vacío para predeterminado)',
        fr: 'p. ex., gpt-4 (laisser vide pour défaut)',
        de: 'z.B., gpt-4 (leer lassen für Standard)',
        pt: 'ex., gpt-4 (deixe em branco para padrão)',
        la: 'e.g., gpt-4 (vacuum relinque pro praedeterminato)'
    },
    'debug.send_request': {
        en: 'Send Request',
        es: 'Enviar Solicitud',
        fr: 'Envoyer la Requête',
        de: 'Anfrage Senden',
        pt: 'Enviar Solicitação',
        la: 'Petitionem Mittere'
    },
    'debug.sending': {
        en: 'Sending...',
        es: 'Enviando...',
        fr: 'Envoi...',
        de: 'Senden...',
        pt: 'Enviando...',
        la: 'Mittendo...'
    },
    'debug.response': {
        en: 'Response',
        es: 'Respuesta',
        fr: 'Réponse',
        de: 'Antwort',
        pt: 'Resposta',
        la: 'Responsum'
    },
    'debug.failed_fetch': {
        en: 'Failed to fetch debug information',
        es: 'Error al obtener información de depuración',
        fr: 'Échec de la récupération des informations de débogage',
        de: 'Fehler beim Abrufen der Debug-Informationen',
        pt: 'Falha ao obter informações de depuração',
        la: 'Informationes emendationis petere defecit'
    },
    'debug.error_fetching': {
        en: 'Error fetching debug information',
        es: 'Error al obtener información de depuración',
        fr: 'Erreur lors de la récupération des informations de débogage',
        de: 'Fehler beim Abrufen der Debug-Informationen',
        pt: 'Erro ao obter informações de depuração',
        la: 'Error petendo informationes emendationis'
    },
    'debug.user_info': {
        en: 'User Information',
        es: 'Información del Usuario',
        fr: 'Informations Utilisateur',
        de: 'Benutzerinformationen',
        pt: 'Informações do Usuário',
        la: 'Informationes Usoris'
    },
    'debug.session_info': {
        en: 'Session Information',
        es: 'Información de Sesión',
        fr: 'Informations de Session',
        de: 'Sitzungsinformationen',
        pt: 'Informações da Sessão',
        la: 'Informationes Sessionis'
    },
    'debug.passkey_credentials': {
        en: 'Passkey Credentials',
        es: 'Credenciales de Passkey',
        fr: 'Identifiants Passkey',
        de: 'Passkey-Anmeldedaten',
        pt: 'Credenciais de Passkey',
        la: 'Credentiales Clavis'
    },
    'debug.login_attempts': {
        en: 'Recent Login Attempts',
        es: 'Intentos Recientes de Inicio de Sesión',
        fr: 'Tentatives de Connexion Récentes',
        de: 'Letzte Anmeldeversuche',
        pt: 'Tentativas Recentes de Login',
        la: 'Conatus Intrandi Recentes'
    },
    // Additional Error Messages
    'errors.failed_delete_account': {
        en: 'Failed to delete account',
        es: 'Error al eliminar la cuenta',
        fr: 'Échec de la suppression du compte',
        de: 'Konto konnte nicht gelöscht werden',
        pt: 'Falha ao excluir a conta',
        la: 'Rationem delere defecit'
    },
    'errors.select_file': {
        en: 'Please select a file to upload.',
        es: 'Por favor, selecciona un archivo para subir.',
        fr: 'Veuillez sélectionner un fichier à télécharger.',
        de: 'Bitte wählen Sie eine Datei zum Hochladen aus.',
        pt: 'Por favor, selecione um arquivo para enviar.',
        la: 'Fasciculum mittendum elige.'
    },
    'errors.select_cv_file': {
        en: 'Please select a CV file to upload.',
        es: 'Por favor, selecciona un archivo de CV para subir.',
        fr: 'Veuillez sélectionner un fichier CV à télécharger.',
        de: 'Bitte wählen Sie eine CV-Datei zum Hochladen aus.',
        pt: 'Por favor, selecione um arquivo de CV para enviar.',
        la: 'Fasciculum CV mittendum elige.'
    },
    'errors.failed_save_profile': {
        en: 'Failed to save profile',
        es: 'Error al guardar el perfil',
        fr: 'Échec de l\'enregistrement du profil',
        de: 'Profil konnte nicht gespeichert werden',
        pt: 'Falha ao salvar o perfil',
        la: 'Professionem servare defecit'
    },
    'errors.failed_linkedin_auth': {
        en: 'Failed to complete LinkedIn authentication',
        es: 'Error al completar la autenticación de LinkedIn',
        fr: 'Échec de l\'authentification LinkedIn',
        de: 'LinkedIn-Authentifizierung fehlgeschlagen',
        pt: 'Falha ao completar autenticação do LinkedIn',
        la: 'Authentificationem LinkedIn perficere defecit'
    },
    'errors.failed_fetch_jobs': {
        en: 'Failed to fetch jobs',
        es: 'Error al obtener empleos',
        fr: 'Échec de la récupération des emplois',
        de: 'Fehler beim Abrufen von Stellen',
        pt: 'Falha ao buscar vagas',
        la: 'Opera petere defecit'
    },
    'errors.failed_generate_offers': {
        en: 'Failed to generate offers',
        es: 'Error al generar ofertas',
        fr: 'Échec de la génération des offres',
        de: 'Fehler beim Erstellen von Angeboten',
        pt: 'Falha ao gerar ofertas',
        la: 'Offerta generare defecit'
    },
    'errors.error_generating_offers': {
        en: 'Error generating offers',
        es: 'Error al generar ofertas',
        fr: 'Erreur lors de la génération des offres',
        de: 'Fehler beim Erstellen von Angeboten',
        pt: 'Erro ao gerar ofertas',
        la: 'Error generando offerta'
    },
    'errors.failed_linkedin_link': {
        en: 'Failed to initiate LinkedIn linking',
        es: 'Error al iniciar la vinculación de LinkedIn',
        fr: 'Échec du lancement de la liaison LinkedIn',
        de: 'Fehler beim Starten der LinkedIn-Verknüpfung',
        pt: 'Falha ao iniciar vinculação do LinkedIn',
        la: 'Conexionem LinkedIn initiare defecit'
    },
    'errors.linkedin_signin_failed': {
        en: 'Failed to sign in with LinkedIn',
        es: 'Error al iniciar sesión con LinkedIn',
        fr: 'Échec de la connexion avec LinkedIn',
        de: 'Fehler beim Anmelden mit LinkedIn',
        pt: 'Falha ao entrar com LinkedIn',
        la: 'Intrare cum LinkedIn defecit'
    },
    'errors.linkedin_signin_initiate_failed': {
        en: 'Failed to initiate LinkedIn sign in',
        es: 'Error al iniciar sesión con LinkedIn',
        fr: 'Échec du lancement de la connexion LinkedIn',
        de: 'Fehler beim Starten der LinkedIn-Anmeldung',
        pt: 'Falha ao iniciar entrada do LinkedIn',
        la: 'Initiare intrare cum LinkedIn defecit'
    },
    'errors.failed_model_response': {
        en: 'Failed to get response from model',
        es: 'Error al obtener respuesta del modelo',
        fr: 'Échec de l\'obtention de la réponse du modèle',
        de: 'Fehler beim Abrufen der Modellantwort',
        pt: 'Falha ao obter resposta do modelo',
        la: 'Responsum ab exemplari petere defecit'
    },
    'errors.error_sending_request': {
        en: 'Error sending request to model',
        es: 'Error al enviar solicitud al modelo',
        fr: 'Erreur lors de l\'envoi de la requête au modèle',
        de: 'Fehler beim Senden der Anfrage an das Modell',
        pt: 'Erro ao enviar solicitação ao modelo',
        la: 'Error mittendo petitionem ad exemplar'
    },
    // CV Score Card
    'cv_score.title': {
        en: 'CV Score',
        es: 'Puntuación del CV',
        fr: 'Score du CV',
        de: 'Lebenslauf-Bewertung',
        pt: 'Pontuação do CV',
        la: 'Punctum Curriculum'
    },
    'cv_score.no_cv': {
        en: 'Upload a CV to get your score',
        es: 'Sube un CV para obtener tu puntuación',
        fr: 'Téléchargez un CV pour obtenir votre score',
        de: 'Laden Sie einen Lebenslauf hoch, um Ihre Bewertung zu erhalten',
        pt: 'Envie um CV para obter sua pontuação',
        la: 'Curriculum mitte ut punctum tuum accipias'
    },
    'cv_score.evaluating': {
        en: 'Analyzing your CV, come back in a few minutes...',
        es: 'Analizando tu CV, vuelve en unos minutos...',
        fr: 'Analyse de votre CV, revenez dans quelques minutes...',
        de: 'Analysiere Ihren Lebenslauf, kommen Sie in ein paar Minuten zurück...',
        pt: 'Analisando seu CV, volte em alguns minutos...',
        la: 'Curriculum tuum examinando, post paucos minutos redi...'
    },
    'cv_score.no_evaluation': {
        en: 'No CV evaluation yet',
        es: 'Aún sin evaluación de CV',
        fr: 'CV pas encore évalué',
        de: 'Noch keine Lebenslauf-Bewertung',
        pt: 'CV ainda não avaliado',
        la: 'Curriculum nondum aestimatum'
    },
    'cv_score.evaluation_failed': {
        en: 'CV evaluation failed. Please try again.',
        es: 'La evaluación del CV falló. Por favor, inténtelo de nuevo.',
        fr: 'L\'évaluation du CV a échoué. Veuillez réessayer.',
        de: 'Die Lebenslauf-Bewertung ist fehlgeschlagen. Bitte versuchen Sie es erneut.',
        pt: 'A avaliação do CV falhou. Por favor, tente novamente.',
        la: 'Aestimatio curriculi defecit. Quaeso iterum temptes.'
    },
    'cv_score.evaluate_now': {
        en: 'Evaluate Now',
        es: 'Evaluar Ahora',
        fr: 'Évaluer Maintenant',
        de: 'Jetzt Bewerten',
        pt: 'Avaliar Agora',
        la: 'Aestima Nunc'
    },
    'cv_score.completeness': {
        en: 'Completeness',
        es: 'Completitud',
        fr: 'Complétude',
        de: 'Vollständigkeit',
        pt: 'Completude',
        la: 'Integritas'
    },
    'cv_score.experience': {
        en: 'Experience Quality',
        es: 'Calidad de Experiencia',
        fr: 'Qualité de l\'Expérience',
        de: 'Erfahrungsqualität',
        pt: 'Qualidade da Experiência',
        la: 'Qualitas Experientiae'
    },
    'cv_score.skills': {
        en: 'Skills Relevance',
        es: 'Relevancia de Habilidades',
        fr: 'Pertinence des Compétences',
        de: 'Relevanz der Fähigkeiten',
        pt: 'Relevância das Habilidades',
        la: 'Pertinentia Artium'
    },
    'cv_score.impact': {
        en: 'Impact Evidence',
        es: 'Evidencia de Impacto',
        fr: 'Preuve d\'Impact',
        de: 'Wirkungsnachweis',
        pt: 'Evidência de Impacto',
        la: 'Testimonium Impactus'
    },
    'cv_score.clarity': {
        en: 'Clarity',
        es: 'Claridad',
        fr: 'Clarté',
        de: 'Klarheit',
        pt: 'Clareza',
        la: 'Claritas'
    },
    'cv_score.consistency': {
        en: 'Consistency',
        es: 'Consistencia',
        fr: 'Cohérence',
        de: 'Konsistenz',
        pt: 'Consistência',
        la: 'Constantia'
    },
    'cv_score.recommendations': {
        en: 'Recommendations',
        es: 'Recomendaciones',
        fr: 'Recommandations',
        de: 'Empfehlungen',
        pt: 'Recomendações',
        la: 'Commendationes'
    },
    'cv_score.re_evaluate': {
        en: 'Re-evaluate CV',
        es: 'Reevaluar CV',
        fr: 'Réévaluer le CV',
        de: 'Lebenslauf neu bewerten',
        pt: 'Reavaliar CV',
        la: 'Curriculum Rursus Examinare'
    },
    'cv_score.view_profile_hub': {
        en: 'View Profile Hub',
        es: 'Ver Centro de Perfil',
        fr: 'Voir le Hub Profil',
        de: 'Profil-Hub anzeigen',
        pt: 'Ver Hub do Perfil',
        la: 'Videre Centrum Profili'
    },
    // Header Navigation
    'header.home': {
        en: 'Home',
        es: 'Inicio',
        fr: 'Accueil',
        de: 'Startseite',
        pt: 'Início',
        la: 'Domus'
    },
    'header.jobs': {
        en: 'Jobs',
        es: 'Empleos',
        fr: 'Emplois',
        de: 'Stellen',
        pt: 'Vagas',
        la: 'Opera'
    },
    'header.metiers': {
        en: 'Occupations',
        es: 'Profesiones',
        fr: 'Metiers',
        de: 'Berufe',
        pt: 'Profissoes',
        la: 'Artes'
    },
    'header.profile_hub': {
        en: 'Profile Hub',
        es: 'Centro de Perfil',
        fr: 'Hub Profil',
        de: 'Profil-Hub',
        pt: 'Hub do Perfil',
        la: 'Centrum Profili'
    },
    // Profile Hub Page
    'profile_hub.title': {
        en: 'Profile Hub',
        es: 'Centro de Perfil',
        fr: 'Hub Profil',
        de: 'Profil-Hub',
        pt: 'Hub do Perfil',
        la: 'Centrum Profili'
    },
    'profile_hub.subtitle': {
        en: 'Your career insights and tools in one place',
        es: 'Tus perspectivas profesionales y herramientas en un solo lugar',
        fr: 'Vos insights de carrière et outils en un seul endroit',
        de: 'Ihre Karriere-Einblicke und Tools an einem Ort',
        pt: 'Seus insights de carreira e ferramentas em um só lugar',
        la: 'Perspectiones et instrumenta curriculum tuum uno loco'
    },
    'profile_hub.detailed_analysis': {
        en: 'Detailed Analysis',
        es: 'Análisis Detallado',
        fr: 'Analyse Détaillée',
        de: 'Detaillierte Analyse',
        pt: 'Análise Detalhada',
        la: 'Analysis Accurata'
    },
    'profile_hub.detailed_analysis_desc': {
        en: 'Deep dive into your CV scores with explanations and improvement suggestions',
        es: 'Análisis profundo de tus puntuaciones de CV con explicaciones y sugerencias de mejora',
        fr: 'Analyse approfondie de vos scores CV avec explications et suggestions d\'amélioration',
        de: 'Tiefgehende Analyse Ihrer Lebenslauf-Bewertungen mit Erklärungen und Verbesserungsvorschlägen',
        pt: 'Análise profunda de suas pontuações de CV com explicações e sugestões de melhoria',
        la: 'Analysis profunda punctorum curriculum cum explicationibus et suggestionibus emendationis'
    },
    'profile_hub.career_path': {
        en: 'Career Path',
        es: 'Trayectoria Profesional',
        fr: 'Parcours de Carrière',
        de: 'Karriereweg',
        pt: 'Trajetória de Carreira',
        la: 'Via Curriculum'
    },
    'profile_hub.career_path_desc': {
        en: 'Visualize potential career progressions based on your experience and skills',
        es: 'Visualiza progresiones profesionales potenciales basadas en tu experiencia y habilidades',
        fr: 'Visualisez les progressions de carrière potentielles basées sur votre expérience et compétences',
        de: 'Visualisieren Sie potenzielle Karriereverläufe basierend auf Ihrer Erfahrung und Fähigkeiten',
        pt: 'Visualize progressões de carreira potenciais com base em sua experiência e habilidades',
        la: 'Videre progressiones curriculum potentiales ex experientia et artibus tuis'
    },
    'profile_hub.skill_gaps': {
        en: 'Skill Gaps',
        es: 'Brechas de Habilidades',
        fr: 'Lacunes de Compétences',
        de: 'Kompetenzlücken',
        pt: 'Lacunas de Habilidades',
        la: 'Lacunae Artium'
    },
    'profile_hub.skill_gaps_desc': {
        en: 'Identify missing skills for your target roles and get learning recommendations',
        es: 'Identifica habilidades faltantes para tus roles objetivo y obtén recomendaciones de aprendizaje',
        fr: 'Identifiez les compétences manquantes pour vos rôles cibles et obtenez des recommandations d\'apprentissage',
        de: 'Identifizieren Sie fehlende Fähigkeiten für Ihre Zielrollen und erhalten Sie Lernempfehlungen',
        pt: 'Identifique habilidades ausentes para seus cargos-alvo e obtenha recomendações de aprendizado',
        la: 'Identifica artes deesse pro muneribus scoporum tuorum et accipe commendationes discendi'
    },
    'profile_hub.cv_templates': {
        en: 'CV Templates',
        es: 'Plantillas de CV',
        fr: 'Modèles de CV',
        de: 'Lebenslauf-Vorlagen',
        pt: 'Modelos de CV',
        la: 'Exemplaria Curriculum'
    },
    'profile_hub.cv_templates_desc': {
        en: 'Access professional CV templates optimized for your industry',
        es: 'Accede a plantillas de CV profesionales optimizadas para tu industria',
        fr: 'Accédez à des modèles de CV professionnels optimisés pour votre industrie',
        de: 'Greifen Sie auf professionelle Lebenslauf-Vorlagen zu, die für Ihre Branche optimiert sind',
        pt: 'Acesse modelos de CV profissionais otimizados para sua indústria',
        la: 'Accede ad exemplaria curriculum professionalia optimata pro industria tua'
    },
    'profile_hub.coming_soon': {
        en: 'Coming Soon',
        es: 'Próximamente',
        fr: 'Bientôt Disponible',
        de: 'Demnächst',
        pt: 'Em Breve',
        la: 'Mox Venturum'
    },
    'profile_hub.tracker': {
        en: 'Tracker',
        es: 'Seguimiento',
        fr: 'Suivi',
        de: 'Tracker',
        pt: 'Rastreador',
        la: 'Segmentator'
    },
    'profile_hub.tracker_desc': {
        en: 'View and manage your favourited occupations, then open the fiche or related job offers',
        es: 'Ve y gestiona tus ocupaciones favoritas, luego abre la ficha o las ofertas relacionadas',
        fr: 'Consultez et gérez vos métiers favoris, puis ouvrez la fiche ou les offres associées',
        de: 'Verwalten Sie Ihre favorisierten Berufe und öffnen Sie die Fiche oder zugehörige Stellenangebote',
        pt: 'Visualize e gerencie suas ocupações favoritas, depois abra a ficha ou ofertas relacionadas',
        la: 'Videre et tractare occupationes gratissimas, deinde fiche vel offertas coniunctas aperire'
    },
    'profile_hub.view_tracker': {
        en: 'View',
        es: 'Ver',
        fr: 'Voir',
        de: 'Anzeigen',
        pt: 'Ver',
        la: 'Videre'
    },

    // Job detail: AI match analysis button
    'analyze_match_ai': {
        en: 'Match Analysis',
        es: 'Análisis de compatibilidad',
        fr: 'Analyse de compatibilité',
        de: 'Matching-Analyse',
        pt: 'Análise de compatibilidade',
        la: 'Analysis congruentiae'
    },

    // Match Analysis Card
    'analysis.title': {
        en: 'Match Analysis',
        es: 'Análisis de Compatibilidad',
        fr: 'Analyse de Compatibilité',
        de: 'Matching-Analyse',
        pt: 'Análise de Compatibilidade',
        la: 'Analysis Congruentiae'
    },
    'analysis.loading': {
        en: 'AI is analyzing your profile...',
        es: 'La IA está analizando tu perfil...',
        fr: 'L\'IA analyse votre profil...',
        de: 'KI analysiert Ihr Profil...',
        pt: 'A IA está analisando seu perfil...',
        la: 'IA profilum tuum examinat...'
    },
    'analysis.technical': {
        en: 'Technical Score',
        es: 'Puntuación Técnica',
        fr: 'Score Technique',
        de: 'Technischer Wert',
        pt: 'Pontuação Técnica',
        la: 'Punctum Technicum'
    },
    'analysis.culture': {
        en: 'Culture Fit',
        es: 'Ajuste Cultural',
        fr: 'Fit Culturel',
        de: 'Kulturelle Passung',
        pt: 'Ajuste Cultural',
        la: 'Congruentia Culturalis'
    },
    'analysis.strengths': {
        en: 'Match Reasons',
        es: 'Puntos Fuertes',
        fr: 'Points Forts',
        de: 'Stärken',
        pt: 'Pontos Fortes',
        la: 'Puncta Fortia'
    },
    'analysis.weaknesses': {
        en: 'Missing / To Improve',
        es: 'A Mejorar / Faltante',
        fr: 'À Améliorer / Manquant',
        de: 'Zu Verbessern',
        pt: 'A Melhorar',
        la: 'Emendandum'
    },
    'analysis.error': {
        en: 'Unable to retrieve analysis.',
        es: 'No se pudo recuperar el análisis.',
        fr: 'Impossible de récupérer l\'analyse.',
        de: 'Analyse fehlgeschlagen.',
        pt: 'Não foi possível recuperar a análise.',
        la: 'Analysis recuperari non potuit.'
    },

    // Detailed Analysis Page
    'detailed_analysis.title': {
        en: 'Detailed CV Analysis',
        es: 'Análisis Detallado del CV',
        fr: 'Analyse Détaillée du CV',
        de: 'Detaillierte Lebenslauf-Analyse',
        pt: 'Análise Detalhada do CV',
        la: 'Analysis Accurata Curriculi'
    },
    'detailed_analysis.loading': {
        en: 'Loading analysis...',
        es: 'Cargando análisis...',
        fr: 'Chargement de l\'analyse...',
        de: 'Analyse wird geladen...',
        pt: 'Carregando análise...',
        la: 'Analysim onerans...'
    },
    'detailed_analysis.error': {
        en: 'Failed to load analysis',
        es: 'Error al cargar el análisis',
        fr: 'Échec du chargement de l\'analyse',
        de: 'Fehler beim Laden der Analyse',
        pt: 'Falha ao carregar análise',
        la: 'Defecit onerans analysim'
    },
    'detailed_analysis.no_evaluation': {
        en: 'No evaluation found. Please evaluate your CV first.',
        es: 'No se encontró evaluación. Por favor, evalúa tu CV primero.',
        fr: 'Aucune évaluation trouvée. Veuillez d\'abord évaluer votre CV.',
        de: 'Keine Bewertung gefunden. Bitte bewerten Sie zuerst Ihren Lebenslauf.',
        pt: 'Nenhuma avaliação encontrada. Por favor, avalie seu CV primeiro.',
        la: 'Nulla aestimatio inventa. Curriculum tuum primum aestima.'
    },
    'detailed_analysis.back': {
        en: 'Back to Profile Hub',
        es: 'Volver al Centro de Perfil',
        fr: 'Retour au Hub Profil',
        de: 'Zurück zum Profil-Hub',
        pt: 'Voltar ao Hub do Perfil',
        la: 'Redire ad Centrum Profili'
    },
    'detailed_analysis.content_analysis': {
        en: 'Content Analysis',
        es: 'Análisis de Contenido',
        fr: 'Analyse du Contenu',
        de: 'Inhaltsanalyse',
        pt: 'Análise de Conteúdo',
        la: 'Analysis Contentus'
    },
    'detailed_analysis.visual_analysis': {
        en: 'Visual Analysis',
        es: 'Análisis Visual',
        fr: 'Analyse Visuelle',
        de: 'Visuelle Analyse',
        pt: 'Análise Visual',
        la: 'Analysis Visualis'
    },
    'detailed_analysis.overall_score': {
        en: 'Overall Score',
        es: 'Puntuación General',
        fr: 'Score Global',
        de: 'Gesamtbewertung',
        pt: 'Pontuação Geral',
        la: 'Punctum Generale'
    },
    'detailed_analysis.dimensions': {
        en: 'Score Dimensions',
        es: 'Dimensiones de Puntuación',
        fr: 'Dimensions du Score',
        de: 'Bewertungsdimensionen',
        pt: 'Dimensões da Pontuação',
        la: 'Dimensiones Puncti'
    },
    'detailed_analysis.evidence': {
        en: 'Evidence',
        es: 'Evidencia',
        fr: 'Preuves',
        de: 'Nachweise',
        pt: 'Evidência',
        la: 'Testimonium'
    },
    'detailed_analysis.content_strengths': {
        en: 'Content Strengths',
        es: 'Fortalezas del Contenido',
        fr: 'Points Forts du Contenu',
        de: 'Inhaltliche Stärken',
        pt: 'Pontos Fortes do Conteúdo',
        la: 'Virtutes Contentus'
    },
    'detailed_analysis.content_weaknesses': {
        en: 'Content Weaknesses',
        es: 'Debilidades del Contenido',
        fr: 'Points Faibles du Contenu',
        de: 'Inhaltliche Schwächen',
        pt: 'Pontos Fracos do Conteúdo',
        la: 'Infirmitates Contentus'
    },
    'detailed_analysis.content_recommendations': {
        en: 'Content Recommendations',
        es: 'Recomendaciones de Contenido',
        fr: 'Recommandations de Contenu',
        de: 'Inhaltsempfehlungen',
        pt: 'Recomendações de Conteúdo',
        la: 'Commendationes Contentus'
    },
    'detailed_analysis.visual_strengths': {
        en: 'Visual Strengths',
        es: 'Fortalezas Visuales',
        fr: 'Points Forts Visuels',
        de: 'Visuelle Stärken',
        pt: 'Pontos Fortes Visuais',
        la: 'Virtutes Visuales'
    },
    'detailed_analysis.visual_weaknesses': {
        en: 'Visual Weaknesses',
        es: 'Debilidades Visuales',
        fr: 'Points Faibles Visuels',
        de: 'Visuelle Schwächen',
        pt: 'Pontos Fracos Visuais',
        la: 'Infirmitates Visuales'
    },
    'detailed_analysis.visual_recommendations': {
        en: 'Visual Recommendations',
        es: 'Recomendaciones Visuales',
        fr: 'Recommandations Visuelles',
        de: 'Visuelle Empfehlungen',
        pt: 'Recomendações Visuais',
        la: 'Commendationes Visuales'
    },
    'detailed_analysis.red_flags': {
        en: 'Red Flags',
        es: 'Señales de Alerta',
        fr: 'Signaux d\'Alerte',
        de: 'Warnzeichen',
        pt: 'Sinais de Alerta',
        la: 'Signa Periculi'
    },
    'detailed_analysis.missing_info': {
        en: 'Missing Information',
        es: 'Información Faltante',
        fr: 'Informations Manquantes',
        de: 'Fehlende Informationen',
        pt: 'Informações Ausentes',
        la: 'Informationes Deesse'
    },
    'detailed_analysis.structured_cv': {
        en: 'Structured CV Data',
        es: 'Datos Estructurados del CV',
        fr: 'Données Structurées du CV',
        de: 'Strukturierte Lebenslaufdaten',
        pt: 'Dados Estruturados do CV',
        la: 'Data Structurata Curriculi'
    },
    'detailed_analysis.personal_info': {
        en: 'Personal Information',
        es: 'Información Personal',
        fr: 'Informations Personnelles',
        de: 'Persönliche Informationen',
        pt: 'Informações Pessoais',
        la: 'Informationes Personales'
    },
    'detailed_analysis.name': {
        en: 'Name',
        es: 'Nombre',
        fr: 'Nom',
        de: 'Name',
        pt: 'Nome',
        la: 'Nomen'
    },
    'detailed_analysis.email': {
        en: 'Email',
        es: 'Correo Electrónico',
        fr: 'Email',
        de: 'E-Mail',
        pt: 'E-mail',
        la: 'Inscriptio Electronica'
    },
    'detailed_analysis.phone': {
        en: 'Phone',
        es: 'Teléfono',
        fr: 'Téléphone',
        de: 'Telefon',
        pt: 'Telefone',
        la: 'Telephonum'
    },
    'detailed_analysis.location': {
        en: 'Location',
        es: 'Ubicación',
        fr: 'Emplacement',
        de: 'Standort',
        pt: 'Localização',
        la: 'Locus'
    },
    'detailed_analysis.portfolio': {
        en: 'Portfolio',
        es: 'Portafolio',
        fr: 'Portfolio',
        de: 'Portfolio',
        pt: 'Portfólio',
        la: 'Theca Operum'
    },
    'detailed_analysis.professional_summary': {
        en: 'Professional Summary',
        es: 'Resumen Profesional',
        fr: 'Résumé Professionnel',
        de: 'Berufliche Zusammenfassung',
        pt: 'Resumo Profissional',
        la: 'Summarium Professionale'
    },
    'detailed_analysis.work_experience': {
        en: 'Work Experience',
        es: 'Experiencia Laboral',
        fr: 'Expérience Professionnelle',
        de: 'Berufserfahrung',
        pt: 'Experiência Profissional',
        la: 'Experientia Laboris'
    },
    'detailed_analysis.present': {
        en: 'Present',
        es: 'Presente',
        fr: 'Présent',
        de: 'Aktuell',
        pt: 'Presente',
        la: 'Praesens'
    },
    'detailed_analysis.education': {
        en: 'Education',
        es: 'Educación',
        fr: 'Formation',
        de: 'Ausbildung',
        pt: 'Educação',
        la: 'Educatio'
    },
    'detailed_analysis.skills': {
        en: 'Skills',
        es: 'Habilidades',
        fr: 'Compétences',
        de: 'Fähigkeiten',
        pt: 'Habilidades',
        la: 'Artes'
    },
    'detailed_analysis.projects': {
        en: 'Projects',
        es: 'Proyectos',
        fr: 'Projets',
        de: 'Projekte',
        pt: 'Projetos',
        la: 'Opera'
    },
    'detailed_analysis.certifications': {
        en: 'Certifications',
        es: 'Certificaciones',
        fr: 'Certifications',
        de: 'Zertifizierungen',
        pt: 'Certificações',
        la: 'Certificationes'
    },
    'detailed_analysis.languages': {
        en: 'Languages',
        es: 'Idiomas',
        fr: 'Langues',
        de: 'Sprachen',
        pt: 'Idiomas',
        la: 'Linguae'
    },
    'detailed_analysis.derived_features': {
        en: 'Derived Insights',
        es: 'Perspectivas Derivadas',
        fr: 'Insights Dérivés',
        de: 'Abgeleitete Erkenntnisse',
        pt: 'Insights Derivados',
        la: 'Perspectiones Derivatae'
    },
    'detailed_analysis.experience_metrics': {
        en: 'Experience Metrics',
        es: 'Métricas de Experiencia',
        fr: 'Métriques d\'Expérience',
        de: 'Erfahrungskennzahlen',
        pt: 'Métricas de Experiência',
        la: 'Metricae Experientiae'
    },
    'detailed_analysis.years_experience': {
        en: 'Years Experience',
        es: 'Años de Experiencia',
        fr: 'Années d\'Expérience',
        de: 'Jahre Erfahrung',
        pt: 'Anos de Experiência',
        la: 'Anni Experientiae'
    },
    'detailed_analysis.positions': {
        en: 'Positions',
        es: 'Puestos',
        fr: 'Postes',
        de: 'Positionen',
        pt: 'Posições',
        la: 'Officia'
    },
    'detailed_analysis.education_entries': {
        en: 'Education Entries',
        es: 'Entradas de Educación',
        fr: 'Entrées d\'Éducation',
        de: 'Bildungseinträge',
        pt: 'Entradas de Educação',
        la: 'Introitus Educationis'
    },
    'detailed_analysis.skills_count': {
        en: 'Skills',
        es: 'Habilidades',
        fr: 'Compétences',
        de: 'Fähigkeiten',
        pt: 'Habilidades',
        la: 'Artes'
    },
    'detailed_analysis.quantified_results': {
        en: 'Quantified Results',
        es: 'Resultados Cuantificados',
        fr: 'Résultats Quantifiés',
        de: 'Quantifizierte Ergebnisse',
        pt: 'Resultados Quantificados',
        la: 'Resultata Quantificata'
    },
    'detailed_analysis.quantified_count': {
        en: 'Quantified achievements found',
        es: 'Logros cuantificados encontrados',
        fr: 'Réalisations quantifiées trouvées',
        de: 'Quantifizierte Erfolge gefunden',
        pt: 'Conquistas quantificadas encontradas',
        la: 'Praestantiae quantificatae inventae'
    },
    'detailed_analysis.timeline_gaps': {
        en: 'Timeline Gaps',
        es: 'Brechas en la Línea de Tiempo',
        fr: 'Lacunes Chronologiques',
        de: 'Zeitliche Lücken',
        pt: 'Lacunas na Linha do Tempo',
        la: 'Lacunae Temporis'
    },
    'detailed_analysis.months': {
        en: 'months',
        es: 'meses',
        fr: 'mois',
        de: 'Monate',
        pt: 'meses',
        la: 'menses'
    },
    'detailed_analysis.between': {
        en: 'Between',
        es: 'Entre',
        fr: 'Entre',
        de: 'Zwischen',
        pt: 'Entre',
        la: 'Inter'
    },
    'detailed_analysis.tenure_analysis': {
        en: 'Tenure Analysis',
        es: 'Análisis de Permanencia',
        fr: 'Analyse de la Durée',
        de: 'Beschäftigungsdaueranalyse',
        pt: 'Análise de Permanência',
        la: 'Analysis Durationis'
    },
    'detailed_analysis.avg_tenure': {
        en: 'Average Tenure',
        es: 'Permanencia Promedio',
        fr: 'Durée Moyenne',
        de: 'Durchschnittliche Beschäftigungsdauer',
        pt: 'Permanência Média',
        la: 'Duratio Media'
    },
    'detailed_analysis.shortest_tenure': {
        en: 'Shortest Tenure',
        es: 'Permanencia Más Corta',
        fr: 'Durée la Plus Courte',
        de: 'Kürzeste Beschäftigungsdauer',
        pt: 'Menor Permanência',
        la: 'Duratio Brevissima'
    },
    'detailed_analysis.longest_tenure': {
        en: 'Longest Tenure',
        es: 'Permanencia Más Larga',
        fr: 'Durée la Plus Longue',
        de: 'Längste Beschäftigungsdauer',
        pt: 'Maior Permanência',
        la: 'Duratio Longissima'
    },
    'detailed_analysis.job_hopping_warning': {
        en: 'Frequent job changes detected',
        es: 'Cambios frecuentes de trabajo detectados',
        fr: 'Changements d\'emploi fréquents détectés',
        de: 'Häufige Jobwechsel erkannt',
        pt: 'Mudanças frequentes de emprego detectadas',
        la: 'Mutationes operis frequentes detectae'
    },
    'detailed_analysis.completeness_flags': {
        en: 'Completeness',
        es: 'Completitud',
        fr: 'Complétude',
        de: 'Vollständigkeit',
        pt: 'Completude',
        la: 'Integritas'
    },
    'detailed_analysis.contact_info': {
        en: 'Contact Info',
        es: 'Información de Contacto',
        fr: 'Coordonnées',
        de: 'Kontaktinformationen',
        pt: 'Informações de Contato',
        la: 'Informationes Contactus'
    },
    'detailed_analysis.summary': {
        en: 'Summary',
        es: 'Resumen',
        fr: 'Résumé',
        de: 'Zusammenfassung',
        pt: 'Resumo',
        la: 'Summarium'
    },
    'detailed_analysis.experience': {
        en: 'Experience',
        es: 'Experiencia',
        fr: 'Expérience',
        de: 'Erfahrung',
        pt: 'Experiência',
        la: 'Experientia'
    },
    'detailed_analysis.education_flag': {
        en: 'Education',
        es: 'Educación',
        fr: 'Formation',
        de: 'Ausbildung',
        pt: 'Educação',
        la: 'Educatio'
    },
    'detailed_analysis.skills_flag': {
        en: 'Skills',
        es: 'Habilidades',
        fr: 'Compétences',
        de: 'Fähigkeiten',
        pt: 'Habilidades',
        la: 'Artes'
    },
    'detailed_analysis.assessments': {
        en: 'Visual Assessments',
        es: 'Evaluaciones Visuales',
        fr: 'Évaluations Visuelles',
        de: 'Visuelle Bewertungen',
        pt: 'Avaliações Visuais',
        la: 'Aestimationes Visuales'
    },
    'detailed_analysis.layout_assessment': {
        en: 'Layout',
        es: 'Diseño',
        fr: 'Mise en Page',
        de: 'Layout',
        pt: 'Layout',
        la: 'Dispositio'
    },
    'detailed_analysis.typography_assessment': {
        en: 'Typography',
        es: 'Tipografía',
        fr: 'Typographie',
        de: 'Typografie',
        pt: 'Tipografia',
        la: 'Typographia'
    },
    'detailed_analysis.readability_assessment': {
        en: 'Readability',
        es: 'Legibilidad',
        fr: 'Lisibilité',
        de: 'Lesbarkeit',
        pt: 'Legibilidade',
        la: 'Legibilitas'
    },
    'detailed_analysis.image_quality_notes': {
        en: 'Image Quality Notes',
        es: 'Notas de Calidad de Imagen',
        fr: 'Notes sur la Qualité de l\'Image',
        de: 'Hinweise zur Bildqualität',
        pt: 'Notas de Qualidade da Imagem',
        la: 'Notae Qualitatis Imaginis'
    },
    'detailed_analysis.no_visual_analysis': {
        en: 'Visual analysis not available for this CV. This may be because the CV was uploaded as text only or the visual analysis service is unavailable.',
        es: 'El análisis visual no está disponible para este CV. Esto puede deberse a que el CV se cargó solo como texto o el servicio de análisis visual no está disponible.',
        fr: 'L\'analyse visuelle n\'est pas disponible pour ce CV. Cela peut être dû au fait que le CV a été téléchargé uniquement en texte ou que le service d\'analyse visuelle est indisponible.',
        de: 'Visuelle Analyse für diesen Lebenslauf nicht verfügbar. Dies kann daran liegen, dass der Lebenslauf nur als Text hochgeladen wurde oder der visuelle Analysedienst nicht verfügbar ist.',
        pt: 'Análise visual não disponível para este CV. Isso pode ser porque o CV foi enviado apenas como texto ou o serviço de análise visual está indisponível.',
        la: 'Analysis visualis pro hoc curriculo non praesto est. Hoc fieri potest quia curriculum solum ut textus sublatum est aut servitium analysis visualis non praesto est.'
    },
    'detailed_analysis.first': {
        en: 'First',
        es: 'Primera',
        fr: 'Première',
        de: 'Erste',
        pt: 'Primeira',
        la: 'Prima'
    },
    'detailed_analysis.second': {
        en: 'Second',
        es: 'Segunda',
        fr: 'Deuxième',
        de: 'Zweite',
        pt: 'Segunda',
        la: 'Secunda'
    },
    'detailed_analysis.third': {
        en: 'Third',
        es: 'Tercera',
        fr: 'Troisième',
        de: 'Dritte',
        pt: 'Terceira',
        la: 'Tertia'
    },
    'detailed_analysis.fourth': {
        en: 'Fourth',
        es: 'Cuarta',
        fr: 'Quatrième',
        de: 'Vierte',
        pt: 'Quarta',
        la: 'Quarta'
    },
    'detailed_analysis.fifth': {
        en: 'Fifth',
        es: 'Quinta',
        fr: 'Cinquième',
        de: 'Fünfte',
        pt: 'Quinta',
        la: 'Quinta'
    },
    'detailed_analysis.ordinal_suffix': {
        en: 'th',
        es: 'ª',
        fr: 'ème',
        de: 'te',
        pt: 'ª',
        la: 'a'
    },
    'detailed_analysis.date_issues': {
        en: 'Date Format Issues',
        es: 'Problemas de Formato de Fecha',
        fr: 'Problèmes de Format de Date',
        de: 'Datumsformatprobleme',
        pt: 'Problemas de Formato de Data',
        la: 'Problema Formati Temporis'
    },
    'detailed_analysis.validation_warnings': {
        en: 'Validation Warnings',
        es: 'Advertencias de Validación',
        fr: 'Avertissements de Validation',
        de: 'Validierungswarnungen',
        pt: 'Avisos de Validação',
        la: 'Admonitiones Validationis'
    },
    'detailed_analysis.timeline_overlaps': {
        en: 'Timeline Overlaps',
        es: 'Superposiciones en la Línea de Tiempo',
        fr: 'Chevauchements Chronologiques',
        de: 'Zeitliche Überschneidungen',
        pt: 'Sobreposições na Linha do Tempo',
        la: 'Superpositiones Temporis'
    },
    'profile_hub.view_analysis': {
        en: 'View Analysis',
        es: 'Ver Análisis',
        fr: 'Voir l\'Analyse',
        de: 'Analyse Anzeigen',
        pt: 'Ver Análise',
        la: 'Videre Analysim'
    },
    'additional_info.title': {
        en: 'Additional Information',
        es: 'Información Adicional',
        fr: 'Informations Supplémentaires',
        de: 'Zusätzliche Informationen',
        pt: 'Informações Adicionais',
        la: 'Informationes Addendae'
    },
    'additional_info.description': {
        en: 'Add details to improve job matching.',
        es: 'Añade detalles para mejorar la búsqueda.',
        fr: 'Ajoutez des détails pour améliorer la recherche.',
        de: 'Details hinzufügen für bessere Ergebnisse.',
        pt: 'Adicione detalhes para melhorar a busca.',
        la: 'Adde particulas ad meliorem inquisitionem.'
    },
    'additional_info.placeholder': {
        en: 'Remote work, Python, startups...',
        es: 'Trabajo remoto, Python, startups...',
        fr: 'Télétravail, Python, startups...',
        de: 'Remote, Python, Startups...',
        pt: 'Remoto, Python, startups...',
        la: 'Remotum, Python, nova...'
    },
    'additional_info.save': {
        en: 'Save',
        es: 'Guardar',
        fr: 'Enregistrer',
        de: 'Speichern',
        pt: 'Salvar',
        la: 'Servare'
    },
    'additional_info.saving': {
        en: 'Saving...',
        es: 'Guardando...',
        fr: 'Enregistrement...',
        de: 'Speichern...',
        pt: 'Salvando...',
        la: 'Servando...'
    },
    'additional_info.saved': {
        en: 'Saved',
        es: 'Guardado',
        fr: 'Enregistré',
        de: 'Gespeichert',
        pt: 'Salvo',
        la: 'Servatum'
    },
    // Tracker (Favourite Occupations) page
    'tracker.title': {
        en: 'Tracker',
        es: 'Seguimiento',
        fr: 'Suivi',
        de: 'Tracker',
        pt: 'Rastreador',
        la: 'Segmentator'
    },
    'tracker.loading': {
        en: 'Loading...',
        es: 'Cargando...',
        fr: 'Chargement...',
        de: 'Laden...',
        pt: 'Carregando...',
        la: 'Onerans...'
    },
    'tracker.back': {
        en: 'Back to Profile Hub',
        es: 'Volver al Centro de Perfil',
        fr: 'Retour au Hub Profil',
        de: 'Zurück zum Profil-Hub',
        pt: 'Voltar ao Hub do Perfil',
        la: 'Redire ad Centrum Profili'
    },
    'tracker.back_to_list': {
        en: 'Back to Tracker',
        es: 'Volver al Seguimiento',
        fr: 'Retour au Suivi',
        de: 'Zurück zum Tracker',
        pt: 'Voltar ao Rastreador',
        la: 'Redire ad Segmentator'
    },
    'tracker.empty': {
        en: 'No tracked occupations yet. Add some from the Occupations tab.',
        es: 'Aún no hay ocupaciones seguidas. Añade algunas desde la pestaña Ocupaciones.',
        fr: 'Aucun métier suivi pour l\'instant. Ajoutez-en depuis l\'onglet Métiers.',
        de: 'Noch keine verfolgten Berufe. Fügen Sie welche im Bereich Berufe hinzu.',
        pt: 'Nenhuma ocupação rastreada ainda. Adicione algumas na aba Ocupações.',
        la: 'Nondum occupationes tractatae. Adde ex tab Occupationum.'
    },
    'tracker.occupations_section': {
        en: 'Occupations',
        es: 'Ocupaciones',
        fr: 'Métiers',
        de: 'Berufe',
        pt: 'Ocupações',
        la: 'Occupationes'
    },
    'tracker.jobs_section': {
        en: 'Jobs',
        es: 'Empleos',
        fr: 'Offres d\'emploi',
        de: 'Stellenangebote',
        pt: 'Vagas',
        la: 'Officia'
    },
    'tracker.empty_occupations': {
        en: 'No tracked occupations yet. Add some from the Occupations tab.',
        es: 'Aún no hay ocupaciones seguidas. Añade algunas desde la pestaña Ocupaciones.',
        fr: 'Aucun métier suivi pour l\'instant. Ajoutez-en depuis l\'onglet Métiers.',
        de: 'Noch keine verfolgten Berufe. Fügen Sie welche im Bereich Berufe hinzu.',
        pt: 'Nenhuma ocupação rastreada ainda. Adicione algumas na aba Ocupações.',
        la: 'Nondum occupationes tractatae. Adde ex tab Occupationum.'
    },
    'tracker.empty_jobs': {
        en: 'No tracked jobs yet. Add some from the Jobs page when viewing an offer.',
        es: 'Aún no hay empleos seguidos. Añade algunos desde la página Empleos al ver una oferta.',
        fr: 'Aucune offre suivie pour l\'instant. Ajoutez-en depuis la page Emploi en consultant une offre.',
        de: 'Noch keine verfolgten Stellen. Fügen Sie welche auf der Stellen-Seite beim Ansehen einer Anzeige hinzu.',
        pt: 'Nenhuma vaga rastreada ainda. Adicione algumas na página Vagas ao ver uma oferta.',
        la: 'Nondum officia tractata. Adde ex pagina Officiorum offerta visa.'
    },
    'tracker.view_job': {
        en: 'View job',
        es: 'Ver empleo',
        fr: 'Voir l\'offre',
        de: 'Stelle anzeigen',
        pt: 'Ver vaga',
        la: 'Officium videre'
    },
    'tracker.browse_jobs': {
        en: 'Browse Jobs',
        es: 'Explorar Empleos',
        fr: 'Parcourir les offres',
        de: 'Stellen durchsuchen',
        pt: 'Explorar Vagas',
        la: 'Officia Perlegere'
    },
    'tracker.browse_occupations': {
        en: 'Browse Occupations',
        es: 'Explorar Ocupaciones',
        fr: 'Parcourir les Métiers',
        de: 'Berufe durchsuchen',
        pt: 'Explorar Ocupações',
        la: 'Occupationes Perlegere'
    },
    'tracker.view_fiche': {
        en: 'View fiche',
        es: 'Ver ficha',
        fr: 'Voir la fiche',
        de: 'Fiche anzeigen',
        pt: 'Ver ficha',
        la: 'Fiche videre'
    },
    'tracker.remove': {
        en: 'Remove from favourites',
        es: 'Quitar de favoritos',
        fr: 'Retirer des favoris',
        de: 'Aus Favoriten entfernen',
        pt: 'Remover dos favoritos',
        la: 'E gratissimis removere'
    }
};

// LanguageContext is now defined and exported from LanguageCore.ts

const detectBrowserLanguage = (): Exclude<Language, 'auto'> => {
    const browserLang = navigator.language.split('-')[0];
    const supportedLangs: Array<Exclude<Language, 'auto'>> = ['en', 'es', 'fr', 'de', 'pt', 'la'];
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
