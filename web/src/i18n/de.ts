import type { Messages } from "./en";

export const de: Messages = {
  meta: {
    title: "Vigilo: kostenloser Sicherheitscheck für Websites",
    description:
      "Prüfen Sie Zertifikat, Sicherheitsheader und offen liegende Dateien Ihrer Website und erhalten Sie die passenden Korrekturen. Kostenlos, passiv, nichts wird gespeichert.",
    methodTitle: "Methode · Vigilo",
  },
  nav: {
    label: "Hauptnavigation",
    newCheck: "Neue Prüfung",
    method: "Methode",
    source: "Quellcode",
    language: "Sprache",
  },
  footer: {
    note: "Kostenlos und Open Source. Prüfen Sie nur Websites, die Sie betreiben oder prüfen dürfen.",
  },
  home: {
    rail: "Check",
    title: "Prüfen Sie die Sicherheit Ihrer Website",
    intro:
      "Vigilo untersucht das Zertifikat Ihrer Website, ihre Sicherheitseinstellungen und Dateien, die nicht öffentlich sein sollten. Sie erhalten einen verständlichen Bericht mit den nötigen Korrekturen. Das dauert etwa 20 Sekunden.",
    scopeLabel: "Umfang",
    scope: [
      {
        term: "Geprüft",
        text: "Zertifikat und Verschlüsselung, Sicherheitsheader, sensible Dateien, E-Mail-Sicherheit, Website-Plattform, Datenschutz-Grundlagen.",
      },
      {
        term: "Nicht geprüft",
        text: "Ihr Code, Ihre Plugins, Passwörter oder Formulare. Es wird nie ein Angriff versucht.",
      },
      { term: "Gespeichert", text: "Nichts auf unseren Servern. Der Bericht verschwindet, wenn Sie die Seite schließen." },
    ],
    methodLink: "So funktioniert die Prüfung",
  },
  form: {
    urlLabel: "Website-Adresse",
    urlHint: "Zum Beispiel example.com oder https://www.example.com",
    authorize: "Ich betreibe diese Website oder darf sie prüfen.",
    submit: "Website prüfen",
  },
  validation: {
    emptyUrl: "Geben Sie eine Website-Adresse ein, zum Beispiel example.com.",
    notAuthorized: "Bitte bestätigen Sie, dass Sie diese Website betreiben oder sie prüfen dürfen.",
  },
  scan: {
    rail: "Läuft",
    title: (host: string) => `Prüfung von ${host}`,
    intro: "Jeder Schritt erscheint unten, während er läuft. Schließen Sie die Seite nicht.",
    logLabel: "Prüfprotokoll",
    states: {
      pending: "wartet",
      running: "läuft",
      done: "fertig",
      failed: "fehlgeschlagen",
    },
  },
  errors: {
    rail: "Abgebrochen",
    title: "Die Prüfung konnte nicht abgeschlossen werden",
    network:
      "Der Vigilo-Dienst ist nicht erreichbar. Prüfen Sie Ihre Internetverbindung oder versuchen Sie es in einer Minute erneut.",
    retry: "Erneut versuchen",
    edit: "Adresse ändern",
  },
  report: {
    rail: "Bericht",
    title: "Sicherheitscheck",
    checkedOn: "Geprüft am",
    method: "Methode",
    methodValue: "Passiv. Eine Anfrage pro Ressource. Kein Angriff getestet.",
    kept: "Gespeichert",
    keptValue: "Nichts auf unseren Servern. Dieser Bericht verschwindet, wenn Sie die Seite schließen, außer Sie lassen diesen Browser eine Zusammenfassung merken.",
    downloadPdf: "PDF herunterladen",
    preparingPdf: "PDF wird erstellt…",
    pdfFailed: "Das PDF konnte nicht erstellt werden. Versuchen Sie es gleich noch einmal.",
    newCheck: "Andere Website prüfen",
    grade: "Note",
    gradeLabel: (grade: string) => `Note ${grade}`,
    issuesCount: (n: number) =>
      n === 0 ? "Nichts zu beheben" : n === 1 ? "1 Punkt zu beheben" : `${n} Punkte zu beheben`,
    observed: "Festgestellt",
    why: "Warum das wichtig ist",
    fix: "So beheben Sie es, je nach Hosting",
    fixFallback: "So beheben Sie es",
    then: "Danach:",
    copy: "Kopieren",
    copied: "Kopiert",
    copiedAnnouncement: "Code in die Zwischenablage kopiert.",
    allClear:
      "Kein Problem gefunden. Halten Sie Ihre Software aktuell und prüfen Sie in einigen Monaten erneut.",
    passed: (n: number) => (n === 1 ? "1 Prüfung bestanden" : `${n} Prüfungen bestanden`),
    notChecked: (n: number) =>
      n === 1 ? "1 Prüfung konnte nicht laufen" : `${n} Prüfungen konnten nicht laufen`,
    notCheckedIntro:
      "Diese Ergebnisse fehlen, die Note ist daher vielleicht zu optimistisch. Versuchen Sie es später erneut.",
    hostingNote: "Ihre Hosting-Auswahl gilt für alle Abschnitte.",
    notGraded: "Ohne Wertung",
    notGradedHint: "Rechtlicher Punkt: Er ändert die Note nicht.",
  },
  progress: {
    rail: "Fortschritt",
    title: "Seit Ihrer letzten Prüfung",
    lastCheck: (date: string) => `Letzte Prüfung: ${date}`,
    score: "Punkte",
    grade: "Note",
    fixed: (n: number) => (n === 1 ? "1 Problem behoben" : `${n} Probleme behoben`),
    added: (n: number) => (n === 1 ? "1 neues Problem" : `${n} neue Probleme`),
    remaining: (n: number) =>
      n === 0
        ? "Kein Problem vom letzten Mal mehr offen"
        : n === 1
          ? "1 Problem vom letzten Mal noch offen"
          : `${n} Probleme vom letzten Mal noch offen`,
    noChange: "Seit Ihrer letzten Prüfung hat sich nichts geändert.",
    forget: "Diese Website auf diesem Gerät vergessen",
    forgotten: "Von diesem Gerät entfernt. Sonst wurde nichts gespeichert.",
    offerTitle: "Beim nächsten Mal den Fortschritt sehen",
    offerText:
      "Prüfen Sie nach den Korrekturen erneut: Vigilo zeigt dann, was behoben wurde und was neu ist. Dafür speichert dieser Browser eine kurze Zusammenfassung dieses Berichts (Datum, Punkte, Note und die Namen der Probleme). Sie verlässt Ihr Gerät nie.",
    remember: "Auf diesem Gerät merken",
    remembered: "Auf diesem Gerät gespeichert. Prüfen Sie nach Ihren Korrekturen erneut.",
    storageFailed: "Dieser Browser erlaubt kein Speichern (privates Fenster?). Es wurde nichts gespeichert.",
  },
  grades: {
    rail: "Note",
    title: "Was die Note bedeutet",
    intro: "Die Note fasst die gefundenen Sicherheitsprobleme zusammen, von A (am besten) bis F (am schlechtesten).",
    toggle: (grade: string) => `Was bedeutet die Note ${grade}?`,
    hide: "Erklärung ausblenden",
    points: "Punkte",
    thisSite: "Diese Website",
    meanings: {
      A: "Sehr gut. Nur kleine Details zu verbessern.",
      B: "Gut. Einige Punkte, die Sie bei Gelegenheit beheben sollten.",
      C: "Befriedigend. Mehrere Schwächen: Planen Sie die Korrekturen in den nächsten Wochen.",
      D: "Schwach. Ernste Schwächen: Beginnen Sie jetzt mit den schwerwiegendsten Punkten.",
      F: "Mangelhaft. Besucher oder Daten sind ernsthaft gefährdet: Handeln Sie sofort.",
    },
    howCalculated:
      "Jede Website startet mit 100 Punkten. Jedes Problem zieht je nach Schwere Punkte ab: kritisch 40, hoch 20, mittel 10, niedrig 3. Eine Warnung zieht die Hälfte ab. Rechtliche Punkte ändern die Note nicht.",
    yourScore: (score: number) => `Diese Website hat ${score} von 100 Punkten erreicht.`,
  },
  active: {
    rail: "Aktive Prüfung",
    title: "Weiter gehen: verifizierte aktive Prüfung",
    intro:
      "Die Prüfung oben liest nur, was jeder Besucher sehen kann. Eine aktive Prüfung sendet Testanfragen, um Lücken wie Injections oder offen liegende Dateien zu finden. Weil sie wie ein Angriff aussehen kann, führt Vigilo sie nur für eine Domain aus, deren Inhaber nachgewiesen hat, dass er sie kontrolliert.",
    start: "Nachweisen, dass mir diese Domain gehört",
    preparing: "Wird vorbereitet…",
    failed: "Bei uns ist etwas schiefgelaufen. Bitte versuchen Sie es gleich noch einmal.",
    steps: {
      choose: "Bestätigungscode veröffentlichen",
      verify: "Code prüfen",
      verified: "Domain bestätigt",
    },
    stepDone: "erledigt",
    methods: { dns: "DNS-Eintrag", file: "Datei auf der Website" },
    methodHints: {
      dns: "Wenn Sie die DNS-Zone Ihrer Domain bearbeiten können, beim Registrar oder Hoster.",
      file: "Wenn Sie Dateien auf Ihre Website hochladen können, per FTP oder im Hosting-Panel.",
    },
    dnsInstructions: "Fügen Sie diesen Eintrag zur DNS-Zone Ihrer Domain hinzu:",
    dnsDelay: "Ein neuer Eintrag kann bis zu einer Stunde brauchen, bis er sichtbar ist.",
    recordType: "Typ",
    recordName: "Name",
    recordValue: "Wert",
    fileInstructions: "Legen Sie unter dieser Adresse eine Textdatei an, die nur den Code enthält:",
    fileAddress: "Adresse",
    fileContent: "Inhalt",
    expires: (time: string) => `Dieser Code gilt bis ${time}.`,
    verify: "Jetzt prüfen",
    verifying: "Wird geprüft…",
    newCode: "Neuen Code anfordern",
    verified: (domain: string) => `${domain} ist bestätigt`,
    validUntil: (time: string) => `Der Nachweis gilt bis ${time}.`,
    keepProof:
      "Lassen Sie den Eintrag oder die Datei bestehen: Vor jeder aktiven Prüfung wird er erneut kontrolliert. Entfernen Sie ihn, um Ihre Erlaubnis zu widerrufen.",
    comingSoon: "Die aktive Prüfung selbst wird gerade gebaut und ist bald hier verfügbar.",
  },
  severity: {
    critical: "Kritisch",
    high: "Hoch",
    medium: "Mittel",
    low: "Niedrig",
    info: "Info",
    pass: "Bestanden",
    note: "Hinweis",
  },
  platforms: {
    apache: "Apache",
    nginx: "Nginx",
    cloudflare: "Cloudflare",
    wordpress: "WordPress",
  },
  method: {
    rail: "Methode",
    title: "So funktioniert die Prüfung",
    intro:
      "Vigilo betrachtet nur, was der Browser jedes Besuchers sehen kann. Es versucht nie einzudringen, Passwörter zu erraten oder Formulare abzusenden.",
    sections: [
      {
        label: "Was geprüft wird",
        title: "Die genaue Liste",
        items: [
          "HTTPS: Die Website ist überhaupt über eine sichere Verbindung erreichbar.",
          "Zertifikat: von Browsern anerkannt, gilt für die Domain, Tage bis zum Ablauf.",
          "Verschlüsselung: TLS 1.0 und 1.1 abgelehnt, TLS 1.2 und 1.3 angeboten (Regeln der BSI TR-03116-4).",
          "Weiterleitung: Adressen mit http:// werden auf https:// umgeleitet.",
          "Sicherheitsheader der Startseite: Strict-Transport-Security, Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy.",
          "Softwareversionen in den Headern Server und X-Powered-By.",
          "Sensible Dateien: /.git/HEAD, /.git/config, /.env, /backup.zip, /backup.sql, /database.sql, /dump.sql, /wp-config.php.bak.",
          "E-Mail-Sicherheit über das öffentliche DNS: SPF, DMARC und DKIM-Schlüssel unter 15 üblichen Namen. Der E-Mail-Anbieter wird anhand der MX-Einträge erkannt, um einen fertigen SPF-Eintrag vorzuschlagen.",
          "Website-Plattform: WordPress, Joomla, Drupal, PrestaShop, Shopify, Wix, Squarespace oder Webflow, ob die Version sichtbar ist und ob WordPress aktuell ist. Von der Seite eingebundene WordPress-Plugins werden mit ihrer aktuellen Version auf wordpress.org verglichen.",
          "Datenschutz und Pflichtangaben im HTML der Startseite: Schriften von Google, Tracker ohne Einwilligungstool, Link zur Datenschutzerklärung, Impressum für deutsche und österreichische Websites, mentions légales für französische Websites.",
        ],
      },
      {
        label: "Wie",
        title: "Passiv und rücksichtsvoll",
        items: [
          "Eine Anfrage pro Ressource, insgesamt etwa 20, höchstens 3 gleichzeitig, dazu etwa 20 öffentliche DNS-Abfragen für E-Mail-Einträge.",
          "Anfragen geben sich mit dem User-Agent „Vigilo“ zu erkennen.",
          "Jede Anfrage wartet höchstens 10 Sekunden. Es werden höchstens 5 Weiterleitungen verfolgt.",
          "Bei sensiblen Dateien werden nur Statuscode und angegebene Größe gelesen. Der Inhalt wird nie heruntergeladen, angezeigt oder gespeichert.",
          "Adressen in privaten Netzwerken werden abgelehnt, auch nach einer Weiterleitung. Jede Verbindung geht an genau die geprüfte Adresse.",
          "Für die aktuelle WordPress-Version fragt Vigilo die öffentliche API von wordpress.org. Die Antwort wird 6 Stunden zwischengespeichert.",
        ],
      },
      {
        label: "Grenzen",
        title: "Was diese Prüfung nicht sagen kann",
        items: [
          "Sie ist kein Penetrationstest. Eine gute Note heißt nicht, dass eine Website nicht angreifbar ist.",
          "Es werden nur die Header der Startseite gelesen. Andere Seiten können sich anders verhalten.",
          "Manche Server beantworten jede Adresse mit einer Seite. HTML-Antworten werden bei sensiblen Dateien ignoriert, was eine echte Offenlegung verbergen kann.",
          "TLS 1.0 und 1.1 lassen sich nur testen, wenn der prüfende Server sie noch unterstützt. Andernfalls sagt der Bericht das.",
          "Themes, Ihr Code sowie Plugins, die ihre Version verbergen oder nicht auf wordpress.org stehen, werden nicht geprüft. DKIM-Schlüssel mit ungewöhnlichen Namen werden nicht gefunden.",
          "Tracker und Links, die nach dem Laden per JavaScript hinzukommen, werden nicht erkannt.",
          "Rechtliche Punkte suchen nur nach Links auf der Startseite. Sie sind ein Hinweis, keine Rechtsberatung.",
        ],
      },
      {
        label: "Daten",
        title: "Was gespeichert wird",
        items: [
          "Berichte werden nicht auf dem Server gespeichert. Sie existieren nur in Ihrem Browser, bis Sie die Seite schließen.",
          "Wenn Sie Auf diesem Gerät merken wählen, speichert Ihr Browser eine kurze Zusammenfassung des Berichts (Datum, Punkte, Note und die Namen der Probleme), um beim nächsten Mal Ihren Fortschritt zu zeigen. Sie wird nie an Vigilo gesendet, und Diese Website vergessen löscht sie.",
          "Zum Schutz vor Missbrauch zählt der Dienst Prüfungen pro IP-Adresse. Dieser Zähler bleibt 10 Minuten im Arbeitsspeicher und wird dann vergessen.",
          "PDF-Dateien werden beim Herunterladen erstellt und nicht auf dem Server gespeichert. Jeder Bericht trägt eine Signatur, daher lässt sich ein veränderter Bericht nicht als PDF erstellen.",
        ],
      },
      {
        label: "Note",
        title: "So wird die Note berechnet",
        items: [
          "Jede Website startet mit 100 Punkten. Jedes Problem zieht Punkte ab: kritisch 40, hoch 20, mittel 10, niedrig 3. Eine Warnung zieht die Hälfte ab.",
          "Datenschutz- und Rechtspunkte stehen im Bericht, ändern die Note aber nicht.",
        ],
      },
    ],
  },
};
