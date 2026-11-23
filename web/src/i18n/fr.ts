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
      { term: "Conservé", text: "Rien. Le rapport disparaît quand vous fermez la page." },
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
    keptValue: "Rien. Ce rapport disparaît quand vous fermez la page.",
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
      "Vigilo ne regarde que ce que le navigateur de n'importe quel visiteur peut voir. Il n'essaie jamais d'entrer, de deviner des mots de passe ou d'envoyer des formulaires.",
    sections: [
      {
        label: "Ce qui est vérifié",
        title: "La liste exacte",
        items: [
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
        ],
      },
      {
        label: "Données",
        title: "Ce qui est conservé",
        items: [
          "Les rapports ne sont pas conservés. Ils n'existent que dans votre navigateur jusqu'à ce que vous fermiez la page.",
          "Pour éviter les abus, le service compte les analyses par adresse IP. Ce compteur est gardé en mémoire 10 minutes, puis oublié.",
          "Les PDF sont créés au moment du téléchargement et ne sont pas conservés sur le serveur. Chaque rapport porte une signature : un rapport modifié ne peut pas être converti en PDF.",
        ],
      },
      {
        label: "Note",
        title: "Comment la note est calculée",
        items: [
          "Chaque site part de 100 points. Chaque problème retire des points : critique 40, élevé 20, moyen 10, faible 3. Un avertissement en retire la moitié.",
          "Les points de vie privée et juridiques figurent dans le rapport mais ne changent pas la note.",
        ],
      },
    ],
  },
};
