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
      publish: "Verifizierungscode veröffentlichen",
      check: "Vigilo prüft den Code",
      verified: "Domain verifiziert",
    },
    stepDone: "erledigt",
    who: {
      question: "Wer kümmert sich um die Technik Ihrer Website?",
      someone: "Jemand anderes: eine Webagentur, ein Entwickler, ein Bekannter",
      someoneHint: "Vigilo schreibt die Nachricht für Sie. Sie leiten sie nur weiter.",
      me: "Ich mache das selbst",
      meHint: "Drei Wege, den Code zu veröffentlichen, mit Schritt-für-Schritt-Anleitungen.",
    },
    delegate: {
      intro:
        "Senden Sie diese Nachricht an die Person, die Ihre Website betreut. Sie erklärt genau, was zu tun ist, in etwa 2 Minuten. Sie müssen sie nicht verstehen.",
      email: "Per E-Mail senden",
      whatsapp: "Per WhatsApp senden",
      copy: "Nachricht kopieren",
      subject: (domain: string) => `Bitte ${domain} für einen Vigilo-Sicherheitsscan verifizieren`,
      message: (p) =>
        `Hallo,\n\nich möchte einen Vigilo-Sicherheitsscan von ${p.domain} durchführen. Um zu beweisen, dass die Website uns gehört, könntest du EINE dieser drei Sachen erledigen? Das dauert etwa 2 Minuten.\n\n1. HTML-Tag: Füge diese Zeile im Abschnitt <head> der Startseite ein und veröffentliche:\n${p.tag}\n\n2. Oder eine Datei: Lege eine Datei namens ${p.fileName} an, die nur diesen Code enthält:\n${p.code}\nund lege sie in den Hauptordner der Website, sodass sie unter ${p.fileUrl} erreichbar ist.\n\n3. Oder ein DNS-Eintrag: Füge einen TXT-Eintrag namens ${p.dnsName} mit diesem Wert hinzu:\n${p.dnsValue}\n\nDer Code gilt bis ${p.until}. Vigilo prüft selbstständig: sonst ist nichts zu tun.\n\nDanke!`,
    },
    methodsTitle: "Wählen Sie einen Weg, den Code zu veröffentlichen",
    methods: { meta: "HTML-Tag", file: "Datei auf der Website", dns: "DNS-Eintrag" },
    methodHints: {
      meta: "Am einfachsten: eine Zeile in den Einstellungen Ihrer Website.",
      file: "Wenn Sie Dateien auf Ihre Website hochladen können.",
      dns: "Wenn Sie Ihren Domainnamen verwalten.",
    },
    metaInstructions:
      "Fügen Sie diese Zeile im Abschnitt <head> Ihrer Startseite ein, dann speichern und veröffentlichen:",
    metaLabel: "Tag",
    fileInstructions:
      "Laden Sie diese Datei herunter und legen Sie sie in den Hauptordner Ihrer Website, den mit der Startseite. Sie muss dann unter dieser Adresse erreichbar sein:",
    download: (name: string) => `${name} herunterladen`,
    fileAddress: "Adresse",
    dnsInstructions: "Fügen Sie diesen Eintrag zur DNS-Zone Ihrer Domain hinzu:",
    dnsDelay: "Ein neuer Eintrag kann bis zu einer Stunde brauchen, bis er sichtbar ist.",
    recordType: "Typ",
    recordName: "Name",
    recordValue: "Wert",
    guidesTitle: "Schritt-für-Schritt-Anleitungen",
    guidesFor: "Wo liegt Ihre Website?",
    guidesNote: "Menüs ändern sich ab und zu: Wenn eine Bezeichnung anders ist, nehmen Sie die ähnlichste.",
    guides: {
      meta: [
        {
          name: "WordPress",
          steps: [
            "Öffnen Sie im WordPress-Dashboard Plugins > Neues Plugin hinzufügen und suchen Sie „WPCode“. Installieren und aktivieren Sie es (kostenlos).",
            "Öffnen Sie Code Snippets > Header & Footer.",
            "Fügen Sie den Tag im Feld Header ein und klicken Sie auf Save Changes.",
            "Wenn Ihre Website ein Cache-Plugin nutzt, leeren Sie den Cache.",
          ],
        },
        {
          name: "Joomla, Drupal, PrestaShop oder eigene Website",
          steps: [
            "Öffnen Sie das Template (Theme) der Startseite in Ihrer Verwaltung oder Ihrem Code-Editor.",
            "Suchen Sie die Zeile </head> und fügen Sie den Tag direkt davor ein.",
            "Speichern und veröffentlichen Sie, dann leeren Sie den Cache, falls vorhanden.",
          ],
        },
      ],
      file: [
        {
          name: "Hosting-Verwaltung (cPanel, hPanel, Plesk)",
          steps: [
            "Laden Sie die Datei mit der Schaltfläche oben herunter.",
            "Melden Sie sich in Ihrer Hosting-Verwaltung an und öffnen Sie den Dateimanager.",
            "Öffnen Sie den Hauptordner der Website: meist public_html, www, htdocs oder httpdocs (der Ordner mit index.php oder index.html).",
            "Laden Sie die Datei dort hoch, ohne sie umzubenennen.",
            "Öffnen Sie die oben angezeigte Adresse: Sie sollten den Code sehen.",
          ],
        },
        {
          name: "FTP (FileZilla)",
          steps: [
            "Laden Sie die Datei mit der Schaltfläche oben herunter.",
            "Verbinden Sie sich mit Ihren FTP-Zugangsdaten mit der Website.",
            "Öffnen Sie auf der Serverseite den Ordner mit der Startseite (public_html, www oder htdocs).",
            "Ziehen Sie die Datei hinein und öffnen Sie zur Kontrolle die oben angezeigte Adresse.",
          ],
        },
      ],
      dns: [
        {
          name: "Cloudflare",
          steps: [
            "Melden Sie sich bei dash.cloudflare.com an und wählen Sie Ihre Domain.",
            "Öffnen Sie DNS > Records und klicken Sie auf Add record.",
            "Type: TXT. Name: _vigilo. Content: der oben angezeigte Wert. Klicken Sie auf Save.",
          ],
        },
        {
          name: "OVHcloud",
          steps: [
            "Öffnen Sie im OVHcloud Kundencenter Web Cloud > Domainnamen und wählen Sie Ihre Domain.",
            "Öffnen Sie den Tab DNS-Zone und klicken Sie auf Eintrag hinzufügen.",
            "Wählen Sie TXT, geben Sie _vigilo als Subdomain und den oben angezeigten Wert ein und bestätigen Sie.",
          ],
        },
        {
          name: "GoDaddy",
          steps: [
            "Öffnen Sie Meine Produkte, suchen Sie Ihre Domain und klicken Sie auf DNS.",
            "Klicken Sie auf Neuen Eintrag hinzufügen und wählen Sie TXT.",
            "Name: _vigilo. Wert: der oben angezeigte Wert. Klicken Sie auf Speichern.",
          ],
        },
        {
          name: "IONOS",
          steps: [
            "Öffnen Sie Domains & SSL, wählen Sie Ihre Domain und öffnen Sie DNS.",
            "Klicken Sie auf Eintrag hinzufügen und wählen Sie TXT.",
            "Hostname: _vigilo. Wert: der oben angezeigte Wert. Klicken Sie auf Speichern.",
          ],
        },
        {
          name: "Anderer Anbieter",
          steps: [
            "Melden Sie sich dort an, wo Sie Ihren Domainnamen gekauft haben, und suchen Sie „DNS-Zone“, „DNS-Einträge“ oder „DNS verwalten“.",
            "Fügen Sie einen Eintrag vom Typ TXT hinzu.",
            "Name (oder Host): _vigilo. Manche Anbieter verlangen stattdessen den oben angezeigten vollständigen Namen. Wert: der oben angezeigte Wert.",
            "Speichern Sie. Der Eintrag kann bis zu einer Stunde brauchen, bis er sichtbar ist.",
          ],
        },
      ],
    },
    expires: (time: string) => `Dieser Code gilt bis ${time}.`,
    waiting:
      "Warten auf den Code. Vigilo prüft alle 30 Sekunden selbstständig. Sie können die Seite verlassen und später wiederkommen: Dieser Browser merkt sich den Code, bis er verifiziert ist.",
    lastChecked: (time: string) => `Letzte Prüfung um ${time}: noch nicht veröffentlicht.`,
    paused: "Die automatischen Prüfungen sind pausiert. Klicken Sie auf „Jetzt prüfen“, sobald der Code veröffentlicht ist.",
    verify: "Jetzt prüfen",
    verifying: "Wird geprüft…",
    newCode: "Neuen Code anfordern",
    verified: (domain: string) => `${domain} ist verifiziert`,
    validUntil: (time: string) => `Der Nachweis gilt bis ${time}.`,
    keepProof:
      "Lassen Sie den Tag, die Datei oder den Eintrag bestehen: Er wird vor jedem aktiven Scan erneut geprüft. Entfernen Sie ihn, um Ihre Erlaubnis zu widerrufen.",
    hosted: (platform: string) =>
      `Ihre Website läuft auf ${platform}. ${platform} kümmert sich um die Sicherheit der eigenen Server und erlaubt niemandem, sie zu scannen. Der aktive Scan ist daher nicht möglich. Der Sicherheitscheck oben bleibt gültig.`,
    conditionsTitle: "Bevor Sie beginnen",
    conditions: [
      "Etwa 10 Minuten lang sendet Vigilo mit Nuclei und OWASP ZAP Testanfragen an diese Website.",
      "Es laufen nur ungefährliche Prüfungen: kein Angriff, kein Erraten von Passwörtern, kein Lasttest. Eine empfindliche Website kann trotzdem langsamer werden, wählen Sie also einen ruhigen Zeitpunkt.",
      "Dies ist kein Penetrationstest: Ein gutes Ergebnis beweist nicht, dass die Website nicht angreifbar ist.",
      "Kurz vor dem Start wird der Eigentumsnachweis erneut geprüft. Vigilo speichert Datum, Domain, Nachweis und Ihre IP-Adresse, um festzuhalten, wer den Scan angefordert hat.",
      "Sie bestätigen, dass Sie für diese Website verantwortlich sind und sie testen lassen dürfen.",
    ],
    accept: "Ich habe diese Bedingungen gelesen und möchte diese Website scannen.",
    mustAccept: "Bitte akzeptieren Sie zuerst die Bedingungen.",
    launch: "Aktiven Scan starten",
    launching: "Nachweis wird geprüft…",
    runningTitle: (domain: string) => `Aktiver Scan von ${domain}`,
    runningIntro: "Das dauert etwa 10 Minuten. Lassen Sie diese Seite geöffnet: Der Bericht erscheint am Ende hier.",
    stoppedTitle: "Der aktive Scan wurde beendet",
    retry: "Erneut versuchen",
    reportTitle: "Aktiver Scan",
    reportMethod: "Aktiv, auf einer verifizierten Domain. Ungefährliche Prüfungen mit Nuclei und OWASP ZAP.",
    reportKept: "Nichts auf unseren Servern, außer dem Einwilligungseintrag: Datum, Domain, Nachweis und IP-Adresse.",
    separateGrade: "Diese Note gilt nur für den aktiven Scan. Sie ist von der Note des Sicherheitschecks getrennt.",
    back: "Zurück zum Sicherheitscheck",
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
