import React from "react";
import { useLanguage } from "./contexts/useLanguage";
import { Header } from "./components";

const PrivacyPolicy: React.FC = () => {
    const { t } = useLanguage();

    return (
        <>
            <Header />
            <div className="nb-page nb-card" style={{ maxWidth: '800px', margin: '0 auto' }}>
                <h1>{t('privacy.title')}</h1>
                <p className="nb-text-dim">{t('privacy.last_updated')}: {t('privacy.date')}</p>

                <section style={{ marginTop: '2rem' }}>
                    <h2>{t('privacy.intro_title')}</h2>
                    <p>{t('privacy.intro_text')}</p>
                </section>

                <section style={{ marginTop: '2rem' }}>
                    <h2>{t('privacy.data_collected_title')}</h2>
                    <p>{t('privacy.data_collected_text')}</p>
                    <ul>
                        <li><strong>{t('privacy.account_info')}</strong>: {t('privacy.account_info_desc')}</li>
                        <li><strong>{t('privacy.profile_info')}</strong>: {t('privacy.profile_info_desc')}</li>
                        <li><strong>{t('privacy.auth_info')}</strong>: {t('privacy.auth_info_desc')}</li>
                        <li><strong>{t('privacy.usage_info')}</strong>: {t('privacy.usage_info_desc')}</li>
                    </ul>
                </section>

                <section style={{ marginTop: '2rem' }}>
                    <h2>{t('privacy.how_we_use_title')}</h2>
                    <p>{t('privacy.how_we_use_text')}</p>
                    <ul>
                        <li>{t('privacy.use_1')}</li>
                        <li>{t('privacy.use_2')}</li>
                        <li>{t('privacy.use_3')}</li>
                        <li>{t('privacy.use_4')}</li>
                    </ul>
                </section>

                <section style={{ marginTop: '2rem' }}>
                    <h2>{t('privacy.linkedin_title')}</h2>
                    <p>{t('privacy.linkedin_text')}</p>
                    <ul>
                        <li>{t('privacy.linkedin_1')}</li>
                        <li>{t('privacy.linkedin_2')}</li>
                        <li>{t('privacy.linkedin_3')}</li>
                    </ul>
                    <p>{t('privacy.linkedin_policy')}</p>
                </section>

                <section style={{ marginTop: '2rem' }}>
                    <h2>{t('privacy.data_security_title')}</h2>
                    <p>{t('privacy.data_security_text')}</p>
                </section>

                <section style={{ marginTop: '2rem' }}>
                    <h2>{t('privacy.data_retention_title')}</h2>
                    <p>{t('privacy.data_retention_text')}</p>
                </section>

                <section style={{ marginTop: '2rem' }}>
                    <h2>{t('privacy.your_rights_title')}</h2>
                    <p>{t('privacy.your_rights_text')}</p>
                    <ul>
                        <li><strong>{t('privacy.right_access')}</strong>: {t('privacy.right_access_desc')}</li>
                        <li><strong>{t('privacy.right_deletion')}</strong>: {t('privacy.right_deletion_desc')}</li>
                        <li><strong>{t('privacy.right_correction')}</strong>: {t('privacy.right_correction_desc')}</li>
                    </ul>
                </section>

                <section style={{ marginTop: '2rem' }}>
                    <h2>{t('privacy.cookies_title')}</h2>
                    <p>{t('privacy.cookies_text')}</p>
                </section>

                <section style={{ marginTop: '2rem' }}>
                    <h2>{t('privacy.third_party_title')}</h2>
                    <p>{t('privacy.third_party_text')}</p>
                </section>

                <section style={{ marginTop: '2rem' }}>
                    <h2>{t('privacy.changes_title')}</h2>
                    <p>{t('privacy.changes_text')}</p>
                </section>

                <section style={{ marginTop: '2rem', marginBottom: '2rem' }}>
                    <h2>{t('privacy.contact_title')}</h2>
                    <p>{t('privacy.contact_text')}</p>
                </section>
            </div>
        </>
    );
};

export default PrivacyPolicy;
