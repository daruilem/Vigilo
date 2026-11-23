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
      { term: "Gespeichert", text: "Nichts. Der Bericht verschwindet, wenn Sie die Seite schließen." },
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
    keptValue: "Nichts. Dieser Bericht verschwindet, wenn Sie die Seite schließen.",
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
          "Berichte werden nicht gespeichert. Sie existieren nur in Ihrem Browser, bis Sie die Seite schließen.",
          "Zum Schutz vor Missbrauch zählt der Dienst Prüfungen pro IP-Adresse. Dieser Zähler bleibt 10 Minuten im Arbeitsspeicher und wird dann vergessen.",
          "PDF-Dateien werden beim Herunterladen erstellt und nicht auf dem Server gespeichert. Jeder Bericht trägt eine Signatur, daher lässt sich ein veränderter Bericht nicht als PDF erstellen.",
        ],
      },
      {
        label: "Note",
        title: "So wird die Note berechnet",
        items: [
          "Jede Website startet mit 100 Punkten. Jedes Problem zieht Punkte ab: kritisch 40, hoch 20, mittel 10, niedrig 3. Eine Warnung zieht die Hälfte ab.",
          "A: ab 90. B: 80 bis 89. C: 65 bis 79. D: 50 bis 64. F: unter 50.",
          "Datenschutz- und Rechtspunkte stehen im Bericht, ändern die Note aber nicht.",
        ],
      },
    ],
  },
};
