import type { ReactNode } from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

type FeatureItem = {
    title: string;
    description: ReactNode;
};

const FeatureList: FeatureItem[] = [
    {
        title: 'AI-Powered Job Search',
        description: (
            <>
                Dux analyzes job listings and ranks opportunities to match your profile
                and preferences, helping you find the right roles faster.
            </>
        ),
    },
    {
        title: 'Unified Accounts',
        description: (
            <>
                Connect your accounts like LinkedIn to streamline discovery and
                applications across platforms, all from a single place.
            </>
        ),
    },
    {
        title: 'Fast Uploads & Profile Setup',
        description: (
            <>
                Quickly import resumes and documents to enrich your profile and improve
                matching quality with minimal friction.
            </>
        ),
    },
];

function Feature({ title, description }: FeatureItem) {
    return (
        <div className={clsx('col col--4')}>
            <div className="text--center padding-horiz--md">
                <h3>{title}</h3>
                <p>{description}</p>
            </div>
        </div>
    );
}

export default function HomepageFeatures(): ReactNode {
    return (
        <section className={styles.features}>
            <div className="container">
                <div className="row">
                    {FeatureList.map((props, idx) => (
                        <Feature key={idx} {...props} />
                    ))}
                </div>
            </div>
        </section>
    );
}
