import type { Messages } from "./en";

export const fr: Messages = {
  meta: {
    title: "Vigilo : bilan de sécurité gratuit pour votre site",
    description:
      "Vérifiez le certificat, les en-têtes de sécurité et les fichiers exposés de votre site, avec les corrections à appliquer. Gratuit, passif, rien n'est conservé.",
    methodTitle: "Méthode · Vigilo",
  },
  nav: {
    label: "Principal",
    newCheck: "Nouvelle analyse",
    method: "Méthode",
    source: "Code source",
    language: "Langue",
  },
  footer: {
    note: "Gratuit et open source. N'analysez que les sites que vous gérez ou que vous êtes autorisé à analyser.",
  },
  home: {
    rail: "Bilan",
    title: "Vérifiez la sécurité de votre site",
    intro:
      "Vigilo examine le certificat de votre site, ses réglages de sécurité et les fichiers qui ne devraient pas être publics. Vous recevez un rapport en langage clair, avec les corrections à appliquer. Cela prend environ 20 secondes.",
    scopeLabel: "Périmètre",
    scope: [
      {
        term: "Vérifié",
        text: "Certificat et chiffrement, en-têtes de sécurité, fichiers sensibles, sécurité des e-mails, plateforme du site, bases de la vie privée.",
      },
      {
        term: "Non vérifié",
        text: "Votre code, vos extensions, vos mots de passe ou vos formulaires. Aucune attaque n'est jamais tentée.",
      },
      { term: "Conservé", text: "Rien sur nos serveurs. Le rapport disparaît quand vous fermez la page." },
    ],
    methodLink: "Comment fonctionne l'analyse",
  },
  form: {
    urlLabel: "Adresse du site",
    urlHint: "Par exemple example.com ou https://www.example.com",
    authorize: "Je gère ce site, ou j'ai l'autorisation de l'analyser.",
    submit: "Analyser ce site",
  },
  validation: {
    emptyUrl: "Saisissez l'adresse d'un site, par exemple example.com.",
    notAuthorized: "Confirmez que vous gérez ce site ou que vous avez l'autorisation de l'analyser.",
  },
  scan: {
    rail: "En cours",
    title: (host: string) => `Analyse de ${host}`,
    intro: "Chaque étape s'affiche ci-dessous pendant son exécution. Ne fermez pas la page.",
    logLabel: "Journal de l'analyse",
    states: {
      pending: "en attente",
      running: "en cours",
      done: "terminé",
      failed: "échec",
    },
  },
  errors: {
    rail: "Arrêtée",
    title: "L'analyse n'a pas pu aboutir",
    network:
      "Impossible de joindre le service Vigilo. Vérifiez votre connexion internet, ou réessayez dans une minute.",
    retry: "Réessayer",
    edit: "Modifier l'adresse",
  },
  report: {
    rail: "Rapport",
    title: "Bilan de sécurité",
    checkedOn: "Analysé le",
    method: "Méthode",
    methodValue: "Passive. Une requête par ressource. Aucune attaque testée.",
    kept: "Conservé",
    keptValue: "Rien sur nos serveurs. Ce rapport disparaît quand vous fermez la page, sauf si vous demandez à ce navigateur d'en mémoriser un résumé.",
    downloadPdf: "Télécharger le PDF",
    preparingPdf: "Préparation du PDF…",
    pdfFailed: "Le PDF n'a pas pu être créé. Réessayez dans un instant.",
    newCheck: "Analyser un autre site",
    grade: "Note",
    gradeLabel: (grade: string) => `Note ${grade}`,
    issuesCount: (n: number) =>
      n === 0 ? "Rien à corriger" : n === 1 ? "1 point à corriger" : `${n} points à corriger`,
    observed: "Constaté",
    why: "Pourquoi c'est important",
    fix: "Comment corriger, selon votre hébergement",
    fixFallback: "Comment corriger",
    then: "Ensuite :",
    copy: "Copier",
    copied: "Copié",
    copiedAnnouncement: "Code copié dans le presse-papiers.",
    allClear:
      "Aucun problème trouvé. Gardez vos logiciels à jour et relancez une analyse dans quelques mois.",
    passed: (n: number) => (n === 1 ? "1 vérification réussie" : `${n} vérifications réussies`),
    notChecked: (n: number) =>
      n === 1 ? "1 vérification n'a pas pu être faite" : `${n} vérifications n'ont pas pu être faites`,
    notCheckedIntro:
      "Ces résultats manquent, la note est donc peut-être trop optimiste. Réessayez plus tard.",
    hostingNote: "Votre choix d'hébergement s'applique à toutes les sections.",
    notGraded: "Non noté",
    notGradedHint: "Point juridique : il ne change pas la note.",
  },
  progress: {
    rail: "Progrès",
    title: "Depuis votre dernière vérification",
    lastCheck: (date: string) => `Dernière vérification : ${date}`,
    score: "Score",
    grade: "Note",
    fixed: (n: number) => (n === 1 ? "1 problème corrigé" : `${n} problèmes corrigés`),
    added: (n: number) => (n === 1 ? "1 nouveau problème" : `${n} nouveaux problèmes`),
    remaining: (n: number) =>
      n === 0
        ? "Plus aucun problème de la dernière fois"
        : n === 1
          ? "1 problème de la dernière fois reste à corriger"
          : `${n} problèmes de la dernière fois restent à corriger`,
    noChange: "Rien n'a changé depuis votre dernière vérification.",
    forget: "Oublier ce site sur cet appareil",
    forgotten: "Supprimé de cet appareil. Rien d'autre n'était conservé.",
    offerTitle: "Voir vos progrès la prochaine fois",
    offerText:
      "Après avoir appliqué les corrections, vérifiez à nouveau : Vigilo montrera ce qui a été corrigé et ce qui est nouveau. Pour cela, ce navigateur garde un court résumé de ce rapport (date, score, note et noms des problèmes). Il ne quitte jamais votre appareil.",
    remember: "Mémoriser sur cet appareil",
    remembered: "Enregistré sur cet appareil. Vérifiez à nouveau après vos corrections.",
    storageFailed: "Ce navigateur n'autorise pas l'enregistrement (navigation privée ?). Rien n'a été conservé.",
  },
  grades: {
    rail: "Note",
    title: "Ce que signifie la note",
    intro: "La note résume les problèmes de sécurité trouvés sur le site, de A (la meilleure) à F (la moins bonne).",
    toggle: (grade: string) => `Que signifie la note ${grade} ?`,
    hide: "Masquer l'explication",
    points: "points",
    thisSite: "Ce site",
    meanings: {
      A: "Très bien. Seuls quelques détails à améliorer.",
      B: "Bien. Quelques points à corriger quand vous avez le temps.",
      C: "Moyen. Plusieurs faiblesses : prévoyez les corrections dans les semaines qui viennent.",
      D: "Faible. Des faiblesses sérieuses : commencez dès maintenant par les points les plus graves.",
      F: "Mauvais. Les visiteurs ou les données sont réellement exposés : agissez tout de suite.",
    },
    howCalculated:
      "Chaque site part de 100 points. Chaque problème retire des points selon sa gravité : critique 40, élevé 20, moyen 10, faible 3. Un avertissement en retire la moitié. Les points juridiques ne changent pas la note.",
    yourScore: (score: number) => `Ce site a obtenu ${score} points sur 100.`,
  },
  active: {
    rail: "Analyse active",
    title: "Aller plus loin : analyse active vérifiée",
    intro:
      "Le bilan ci-dessus lit seulement ce que tout visiteur peut voir. Une analyse active envoie des requêtes de test pour trouver des failles comme des injections ou des fichiers exposés. Comme elle peut ressembler à une attaque, Vigilo ne la lance que sur un domaine dont le propriétaire a prouvé qu'il le contrôle.",
    start: "Prouver que ce domaine m'appartient",
    preparing: "Préparation…",
    failed: "Un problème est survenu de notre côté. Réessayez dans un instant.",
    steps: {
      publish: "Publier le code de vérification",
      check: "Vigilo vérifie le code",
      verified: "Domaine vérifié",
    },
    stepDone: "fait",
    who: {
      question: "Qui s'occupe de la partie technique de votre site ?",
      someone: "Quelqu'un d'autre : une agence web, un développeur, un proche",
      someoneHint: "Vigilo rédige le message pour vous. Vous n'avez qu'à le transmettre.",
      me: "Je m'en occupe moi-même",
      meHint: "Trois façons de publier le code, avec des guides pas à pas.",
    },
    delegate: {
      intro:
        "Envoyez ce message à la personne qui s'occupe de votre site. Il lui explique exactement quoi faire, en 2 minutes environ. Vous n'avez pas besoin de le comprendre.",
      email: "Envoyer par e-mail",
      whatsapp: "Envoyer sur WhatsApp",
      copy: "Copier le message",
      subject: (domain: string) => `Merci de vérifier ${domain} pour une analyse de sécurité Vigilo`,
      message: (p) =>
        `Bonjour,\n\nJe voudrais lancer une analyse de sécurité Vigilo de ${p.domain}. Pour prouver que le site est bien à nous, pourrais-tu faire UNE de ces trois choses ? Cela prend environ 2 minutes.\n\n1. Balise HTML : colle cette ligne dans la section <head> de la page d'accueil, puis publie :\n${p.tag}\n\n2. Ou un fichier : crée un fichier nommé ${p.fileName} qui contient uniquement ce code :\n${p.code}\net place-le dans le dossier principal du site, pour qu'il s'ouvre à l'adresse ${p.fileUrl}\n\n3. Ou un enregistrement DNS : ajoute un enregistrement TXT nommé ${p.dnsName} avec cette valeur :\n${p.dnsValue}\n\nLe code est valable jusqu'au ${p.until}. Vigilo vérifie tout seul : rien d'autre à faire.\n\nMerci !`,
    },
    methodsTitle: "Choisissez une façon de publier le code",
    methods: { meta: "Balise HTML", file: "Fichier sur le site", dns: "Enregistrement DNS" },
    methodHints: {
      meta: "La plus simple : une ligne dans les réglages de votre site.",
      file: "Si vous pouvez déposer des fichiers sur votre site.",
      dns: "Si vous gérez votre nom de domaine.",
    },
    metaInstructions:
      "Collez cette ligne dans la section <head> de votre page d'accueil, puis enregistrez et publiez :",
    metaLabel: "Balise",
    fileInstructions:
      "Téléchargez ce fichier et placez-le dans le dossier principal de votre site, celui qui contient la page d'accueil. Il doit ensuite s'ouvrir à cette adresse :",
    download: (name: string) => `Télécharger ${name}`,
    fileAddress: "Adresse",
    dnsInstructions: "Ajoutez cet enregistrement à la zone DNS de votre domaine :",
    dnsDelay: "Un nouvel enregistrement peut mettre jusqu'à une heure à apparaître.",
    recordType: "Type",
    recordName: "Nom",
    recordValue: "Valeur",
    guidesTitle: "Guides pas à pas",
    guidesFor: "Où se trouve votre site ?",
    guidesNote: "Les menus changent de temps en temps : si un libellé est différent, cherchez le plus proche.",
    guides: {
      meta: [
        {
          name: "WordPress",
          steps: [
            "Dans votre tableau de bord WordPress, ouvrez Extensions > Ajouter une extension et cherchez « WPCode ». Installez-la et activez-la (elle est gratuite).",
            "Ouvrez Code Snippets > Header & Footer.",
            "Collez la balise dans la zone Header, puis cliquez sur Save Changes.",
            "Si votre site utilise une extension de cache, videz son cache.",
          ],
        },
        {
          name: "Joomla, Drupal, PrestaShop ou site sur mesure",
          steps: [
            "Ouvrez le modèle (thème) de la page d'accueil dans votre administration ou votre éditeur de code.",
            "Trouvez la ligne </head> et collez la balise juste avant.",
            "Enregistrez et publiez, puis videz le cache s'il y en a un.",
          ],
        },
      ],
      file: [
        {
          name: "Panneau d'hébergement (cPanel, hPanel, Plesk)",
          steps: [
            "Téléchargez le fichier avec le bouton ci-dessus.",
            "Connectez-vous à votre panneau d'hébergement et ouvrez le Gestionnaire de fichiers.",
            "Ouvrez le dossier principal du site : en général public_html, www, htdocs ou httpdocs (celui qui contient index.php ou index.html).",
            "Déposez-y le fichier, sans le renommer.",
            "Ouvrez l'adresse indiquée ci-dessus : vous devez voir le code.",
          ],
        },
        {
          name: "FTP (FileZilla)",
          steps: [
            "Téléchargez le fichier avec le bouton ci-dessus.",
            "Connectez-vous à votre site avec vos identifiants FTP.",
            "Côté serveur, ouvrez le dossier qui contient la page d'accueil (public_html, www ou htdocs).",
            "Glissez-y le fichier, puis ouvrez l'adresse indiquée ci-dessus pour vérifier.",
          ],
        },
      ],
      dns: [
        {
          name: "Cloudflare",
          steps: [
            "Connectez-vous à dash.cloudflare.com et choisissez votre domaine.",
            "Ouvrez DNS > Records et cliquez sur Add record.",
            "Type : TXT. Name : _vigilo. Content : la valeur indiquée ci-dessus. Cliquez sur Save.",
          ],
        },
        {
          name: "OVHcloud",
          steps: [
            "Dans l'espace client OVHcloud, ouvrez Web Cloud > Noms de domaine et choisissez votre domaine.",
            "Ouvrez l'onglet Zone DNS et cliquez sur Ajouter une entrée.",
            "Choisissez TXT, indiquez _vigilo comme sous-domaine et la valeur indiquée ci-dessus, puis validez.",
          ],
        },
        {
          name: "GoDaddy",
          steps: [
            "Ouvrez Mes produits, trouvez votre domaine et cliquez sur DNS.",
            "Cliquez sur Ajouter un nouvel enregistrement et choisissez TXT.",
            "Nom : _vigilo. Valeur : la valeur indiquée ci-dessus. Cliquez sur Enregistrer.",
          ],
        },
        {
          name: "IONOS",
          steps: [
            "Ouvrez Domaines & SSL, choisissez votre domaine, puis ouvrez DNS.",
            "Cliquez sur Ajouter un enregistrement et choisissez TXT.",
            "Nom d'hôte : _vigilo. Valeur : la valeur indiquée ci-dessus. Cliquez sur Enregistrer.",
          ],
        },
        {
          name: "Autre fournisseur",
          steps: [
            "Connectez-vous là où vous avez acheté votre nom de domaine et cherchez « Zone DNS », « Enregistrements DNS » ou « Gérer le DNS ».",
            "Ajoutez un enregistrement de type TXT.",
            "Nom (ou Hôte) : _vigilo. Certains fournisseurs demandent plutôt le nom complet indiqué ci-dessus. Valeur : la valeur indiquée ci-dessus.",
            "Enregistrez. L'enregistrement peut mettre jusqu'à une heure à apparaître.",
          ],
        },
      ],
    },
    expires: (time: string) => `Ce code est valable jusqu'au ${time}.`,
    waiting:
      "En attente du code. Vigilo vérifie tout seul toutes les 30 secondes. Vous pouvez partir et revenir plus tard : ce navigateur garde le code jusqu'à sa vérification.",
    lastChecked: (time: string) => `Dernière vérification à ${time} : pas encore publié.`,
    paused: "Les vérifications automatiques sont en pause. Cliquez sur « Vérifier maintenant » une fois le code publié.",
    verify: "Vérifier maintenant",
    verifying: "Vérification…",
    newCode: "Obtenir un nouveau code",
    verified: (domain: string) => `${domain} est vérifié`,
    validUntil: (time: string) => `La preuve est valable jusqu'au ${time}.`,
    keepProof:
      "Laissez la balise, le fichier ou l'enregistrement en place : il est vérifié à nouveau avant chaque analyse active. Retirez-le pour retirer votre autorisation.",
    hosted: (platform: string) =>
      `Votre site fonctionne sur ${platform}. ${platform} s'occupe de la sécurité de ses propres serveurs et ne permet à personne de les analyser : l'analyse active ne s'applique donc pas. Le bilan ci-dessus reste valable.`,
    conditionsTitle: "Avant de commencer",
    conditions: [
      "Pendant environ 10 minutes, Vigilo envoie des requêtes de test à ce site avec Nuclei et OWASP ZAP.",
      "Seules des vérifications sans danger sont lancées : aucune attaque, aucun essai de mot de passe, aucun test de charge. Un site fragile peut tout de même ralentir : choisissez un moment calme.",
      "Ce n'est pas un test d'intrusion : un bon résultat ne prouve pas que le site ne peut pas être attaqué.",
      "Juste avant le début, la preuve de propriété est vérifiée à nouveau. Vigilo enregistre la date, le domaine, la preuve et votre adresse IP, pour savoir qui a demandé l'analyse.",
      "Vous confirmez être responsable de ce site et avoir le droit de le faire tester.",
    ],
    accept: "J'ai lu ces conditions et je veux analyser ce site.",
    mustAccept: "Acceptez d'abord les conditions.",
    launch: "Lancer l'analyse active",
    launching: "Vérification de la preuve…",
    runningTitle: (domain: string) => `Analyse active de ${domain}`,
    runningIntro: "Cela prend environ 10 minutes. Gardez cette page ouverte : le rapport apparaîtra ici à la fin.",
    stoppedTitle: "L'analyse active s'est arrêtée",
    retry: "Réessayer",
    reportTitle: "Analyse active",
    reportMethod: "Active, sur un domaine vérifié. Vérifications sans danger avec Nuclei et OWASP ZAP.",
    reportKept: "Rien sur nos serveurs, sauf l'enregistrement du consentement : date, domaine, preuve et adresse IP.",
    separateGrade: "Cette note ne concerne que l'analyse active. Elle est distincte de la note du bilan.",
    back: "Retour au bilan",
  },
  severity: {
    critical: "Critique",
    high: "Élevé",
    medium: "Moyen",
    low: "Faible",
    info: "Info",
    pass: "Conforme",
    note: "Remarque",
  },
  platforms: {
    apache: "Apache",
    nginx: "Nginx",
    cloudflare: "Cloudflare",
    wordpress: "WordPress",
  },
  method: {
    rail: "Méthode",
    title: "Comment fonctionne l'analyse",
    intro:
      "Le bilan ne regarde que ce que le navigateur de n'importe quel visiteur peut voir. Il n'essaie jamais d'entrer, de deviner des mots de passe ni d'envoyer des formulaires. L'analyse active, facultative, va plus loin, et seulement pour les propriétaires qui ont prouvé que le domaine est à eux.",
    sections: [
      {
        label: "Ce qui est vérifié",
        title: "La liste exacte",
        items: [
          "HTTPS : le site répond bien par une connexion sécurisée.",
          "Certificat : reconnu par les navigateurs, couvre le domaine, jours avant expiration.",
          "Chiffrement : TLS 1.0 et 1.1 refusés, TLS 1.2 et 1.3 proposés (règles du BSI TR-03116-4).",
          "Redirection : les adresses en http:// sont envoyées vers https://.",
          "En-têtes de sécurité de la page d'accueil : Strict-Transport-Security, Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy.",
          "Versions logicielles affichées dans les en-têtes Server et X-Powered-By.",
          "Fichiers sensibles : /.git/HEAD, /.git/config, /.env, /backup.zip, /backup.sql, /database.sql, /dump.sql, /wp-config.php.bak.",
          "Sécurité des e-mails, via le DNS public : SPF, DMARC, et clés DKIM sous 15 noms courants. Le fournisseur de messagerie est reconnu grâce aux enregistrements MX pour proposer un enregistrement SPF prêt à l'emploi.",
          "Plateforme du site : WordPress, Joomla, Drupal, PrestaShop, Shopify, Wix, Squarespace ou Webflow, affichage de la version, et mise à jour de WordPress. Les extensions WordPress utilisées par la page sont comparées avec leur dernière version sur wordpress.org.",
          "Bases de la vie privée et mentions obligatoires dans le HTML de la page d'accueil : polices chargées depuis Google, traceurs sans outil de consentement, lien vers la politique de confidentialité, Impressum pour les sites allemands et autrichiens, mentions légales pour les sites français.",
        ],
      },
      {
        label: "Comment",
        title: "Passive et respectueuse",
        items: [
          "Une requête par ressource, environ 20 au total, 3 au maximum en même temps, plus une vingtaine de requêtes DNS publiques pour les e-mails.",
          "Les requêtes s'identifient avec le User-Agent « Vigilo ».",
          "Chaque requête attend 10 secondes au maximum. 5 redirections au maximum sont suivies.",
          "Pour les fichiers sensibles, seuls le code de statut et la taille déclarée sont lus. Le contenu n'est jamais téléchargé, affiché ni conservé.",
          "Les adresses pointant vers des réseaux privés sont refusées, y compris après une redirection. Chaque connexion se fait vers l'adresse exacte qui a été vérifiée.",
          "Pour connaître la dernière version de WordPress, Vigilo interroge l'API publique de wordpress.org. La réponse est gardée en cache 6 heures.",
        ],
      },
      {
        label: "Analyse active",
        title: "Aller plus loin, sur des domaines vérifiés seulement",
        items: [
          "Quand ce service la propose, une analyse active facultative envoie des requêtes de test avec deux outils libres reconnus : Nuclei (vulnérabilités connues, fichiers et pages d'administration exposés) et la base d'OWASP ZAP (une courte exploration du site, puis des règles passives). Elle dure environ 10 minutes.",
          "Seules des vérifications sans danger sont lancées : pas de déni de service, pas d'essai de mots de passe, pas de fuzzing, pas d'exploitation et aucun appel à des serveurs extérieurs. 20 requêtes par seconde au maximum.",
          "Elle ne s'exécute que sur un domaine dont le propriétaire a prouvé le contrôle, comme dans Google Search Console : une balise HTML dans la page d'accueil, un fichier à la racine du site ou un enregistrement DNS. Vigilo peut rédiger la demande pour la personne qui gère le site, et cherche le code tout seul.",
          "La preuve est vérifiée à nouveau juste avant chaque analyse : retirer la balise, le fichier ou l'enregistrement retire l'autorisation. Une preuve est valable 24 heures.",
          "Seul le nom exact vérifié est analysé : exemple.fr ne couvre pas boutique.exemple.fr. Les outils ne peuvent pas suivre une redirection vers un autre site.",
          "Chaque outil tourne dans son propre conteneur éphémère et verrouillé, avec une mémoire et une durée limitées, et il est arrêté à la fin.",
          "Les sites sur Shopify, Wix, Squarespace ou Webflow ne se voient pas proposer l'analyse active : elle testerait les serveurs de la plateforme, ce que leurs conditions interdisent.",
          "Les résultats ne gardent que l'adresse, le nom du paramètre et la description du problème par l'outil, jamais de contenu du site. Les problèmes déjà signalés par le bilan ne sont pas comptés deux fois.",
        ],
      },
      {
        label: "Limites",
        title: "Ce que cette analyse ne peut pas vous dire",
        items: [
          "Ce n'est pas un test d'intrusion. Une bonne note ne signifie pas qu'un site est inattaquable.",
          "Seuls les en-têtes de la page d'accueil sont lus. D'autres pages peuvent se comporter autrement.",
          "Certains serveurs répondent à toutes les adresses par une page. Les réponses HTML sont ignorées pour les fichiers sensibles, ce qui peut masquer une vraie exposition.",
          "TLS 1.0 et 1.1 ne peuvent être testés que si le serveur d'analyse les prend encore en charge. Sinon, le rapport l'indique.",
          "Les thèmes, votre code, et les extensions qui masquent leur version ou ne sont pas sur wordpress.org ne sont pas vérifiés. Les clés DKIM aux noms inhabituels ne peuvent pas être trouvées.",
          "Les traceurs et liens ajoutés par JavaScript après le chargement de la page ne sont pas vus.",
          "Les points juridiques ne cherchent que des liens sur la page d'accueil. C'est un rappel, pas un conseil juridique.",
          "L'analyse active n'est pas non plus un test d'intrusion : il n'y a ni humain ni exploitation. Les problèmes qui demandent de se connecter ou d'attaquer des formulaires restent invisibles.",
        ],
      },
      {
        label: "Données",
        title: "Ce qui est conservé",
        items: [
          "Les rapports ne sont pas conservés sur le serveur. Ils n'existent que dans votre navigateur jusqu'à ce que vous fermiez la page.",
          "Si vous choisissez Mémoriser sur cet appareil, votre navigateur garde un court résumé du rapport (date, score, note et noms des problèmes) pour montrer vos progrès la prochaine fois. Il n'est jamais envoyé à Vigilo, et Oublier ce site le supprime.",
          "Pour éviter les abus, le service compte les analyses par adresse IP. Ce compteur est gardé en mémoire 10 minutes, puis oublié.",
          "Les PDF sont créés au moment du téléchargement et ne sont pas conservés sur le serveur. Chaque rapport porte une signature : un rapport modifié ne peut pas être converti en PDF.",
          "Pour chaque analyse active, Vigilo enregistre la date, le domaine, la preuve utilisée et votre adresse IP, pour savoir qui l'a demandée. Rien d'autre n'est conservé sur l'analyse.",
          "Pendant que vous attendez la publication d'un code de vérification, votre navigateur le garde, pour que vous puissiez revenir plus tard. Il est supprimé une fois vérifié ou expiré.",
        ],
      },
      {
        label: "Note",
        title: "Comment la note est calculée",
        items: [
          "Chaque site part de 100 points. Chaque problème retire des points : critique 40, élevé 20, moyen 10, faible 3. Un avertissement en retire la moitié.",
          "Les points de vie privée et juridiques figurent dans le rapport mais ne changent pas la note.",
          "L'analyse active est notée de la même façon, avec sa propre note : la note du bilan reste comparable d'un site à l'autre.",
        ],
      },
    ],
  },
};
