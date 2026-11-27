/**
 * Every piece of interface text lives here. To add a language, copy this file,
 * translate the values and keep the same shape (enforced by the `Messages` type).
 */
import type { ProofMethod } from "@/lib/types";

/** What the message sent to the person who looks after the website contains. */
export interface ProofMessage {
  domain: string;
  tag: string;
  fileName: string;
  fileUrl: string;
  code: string;
  dnsName: string;
  dnsValue: string;
  until: string;
}

/** Steps to publish the code on one kind of hosting. */
export interface Guide {
  name: string;
  steps: string[];
}

export const en = {
  meta: {
    title: "Vigilo: free website security check-up",
    description:
      "Check your website's certificate, security headers and exposed files, and get the fixes to apply. Free, passive, nothing stored.",
    methodTitle: "Method · Vigilo",
  },
  nav: {
    label: "Main",
    newCheck: "New check",
    method: "Method",
    source: "Source code",
    language: "Language",
  },
  footer: {
    note: "Free and open source. Only check websites you run or have permission to check.",
  },
  home: {
    rail: "Check-up",
    title: "Check the security of your website",
    intro:
      "Vigilo looks at your site's certificate, its security settings and files that should not be public. You get a report in plain language, with the fixes to apply. It takes about 20 seconds.",
    scopeLabel: "Scope",
    scope: [
      {
        term: "Checked",
        text: "Certificate and encryption, security headers, sensitive files, email security, website platform, privacy basics.",
      },
      {
        term: "Not checked",
        text: "Your code, plugins, passwords or forms. No attack is ever attempted.",
      },
      { term: "Kept", text: "Nothing on our servers. The report disappears when you close the page." },
    ],
    methodLink: "How the check works",
  },
  form: {
    urlLabel: "Website address",
    urlHint: "For example example.com or https://www.example.com",
    authorize: "I run this website, or I have permission to check it.",
    submit: "Check this website",
  },
  validation: {
    emptyUrl: "Enter a website address, for example example.com.",
    notAuthorized:
      "Please confirm that you run this website or have permission to check it.",
  },
  scan: {
    rail: "In progress",
    title: (host: string) => `Checking ${host}`,
    intro: "Each step appears below as it runs. Do not close the page.",
    logLabel: "Check log",
    states: {
      pending: "waiting",
      running: "in progress",
      done: "done",
      failed: "failed",
    },
  },
  errors: {
    rail: "Stopped",
    title: "The check could not be completed",
    network:
      "We could not reach the Vigilo service. Check your internet connection, or try again in a minute.",
    retry: "Try again",
    edit: "Change the address",
  },
  report: {
    rail: "Report",
    title: "Security check-up",
    checkedOn: "Checked on",
    method: "Method",
    methodValue: "Passive. One request per resource. No attack tested.",
    kept: "Kept",
    keptValue: "Nothing on our servers. This report disappears when you close the page, unless you ask this browser to remember a summary.",
    downloadPdf: "Download PDF",
    preparingPdf: "Preparing the PDF…",
    pdfFailed: "The PDF could not be created. Try again in a moment.",
    newCheck: "Check another website",
    grade: "Grade",
    gradeLabel: (grade: string) => `Grade ${grade}`,
    issuesCount: (n: number) =>
      n === 0 ? "Nothing to fix" : n === 1 ? "1 issue to fix" : `${n} issues to fix`,
    observed: "Observed",
    why: "Why it matters",
    fix: "How to fix it, by hosting",
    fixFallback: "How to fix it",
    then: "Then:",
    copy: "Copy",
    copied: "Copied",
    copiedAnnouncement: "Code copied to the clipboard.",
    allClear: "No problem was found. Keep your software up to date and check again in a few months.",
    passed: (n: number) => (n === 1 ? "1 check passed" : `${n} checks passed`),
    notChecked: (n: number) =>
      n === 1 ? "1 check could not run" : `${n} checks could not run`,
    notCheckedIntro:
      "These results are missing, so the grade may be too optimistic. Try again later.",
    hostingNote: "Your choice of hosting applies to every section.",
    notGraded: "Not graded",
    notGradedHint: "Legal point: it does not change the grade.",
  },
  progress: {
    rail: "Progress",
    title: "Since your last check",
    lastCheck: (date: string) => `Last check: ${date}`,
    score: "Score",
    grade: "Grade",
    fixed: (n: number) => (n === 1 ? "1 problem fixed" : `${n} problems fixed`),
    added: (n: number) => (n === 1 ? "1 new problem" : `${n} new problems`),
    remaining: (n: number) =>
      n === 0
        ? "No problem left from last time"
        : n === 1
          ? "1 problem from last time still to fix"
          : `${n} problems from last time still to fix`,
    noChange: "Nothing changed since your last check.",
    forget: "Forget this website on this device",
    forgotten: "Removed from this device. Nothing else was kept.",
    offerTitle: "See your progress next time",
    offerText:
      "After you apply the fixes, check again: Vigilo will show what was fixed and what is new. For that, this browser keeps a short summary of this report (date, score, grade and the names of the problems). It never leaves your device.",
    remember: "Remember on this device",
    remembered: "Saved on this device. Check again after your fixes.",
    storageFailed: "This browser does not allow saving (private browsing?). Nothing was kept.",
  },
  grades: {
    rail: "Grade",
    title: "What the grade means",
    intro: "The grade sums up the security problems found on the site, from A (best) to F (worst).",
    toggle: (grade: string) => `What does grade ${grade} mean?`,
    hide: "Hide the explanation",
    points: "points",
    thisSite: "This site",
    meanings: {
      A: "Very good. Only small details to improve.",
      B: "Good. A few points to fix when you have time.",
      C: "Fair. Several weaknesses: plan the fixes in the coming weeks.",
      D: "Weak. Serious weaknesses: start with the most severe points now.",
      F: "Poor. Visitors or data are at real risk: act right away.",
    } as Record<string, string>,
    howCalculated:
      "Every site starts with 100 points. Each problem removes points according to its severity: critical 40, high 20, medium 10, low 3. A warning removes half. Legal points do not change the grade.",
    yourScore: (score: number) => `This site scored ${score} points out of 100.`,
  },
  active: {
    rail: "Active scan",
    title: "Go further: verified active scan",
    intro:
      "The check-up above only reads what every visitor can see. An active scan sends test requests to find flaws such as injections or exposed files. Because it can look like an attack, Vigilo only runs it on a domain whose owner has proved control of it.",
    start: "Prove that I own this domain",
    preparing: "Preparing…",
    failed: "Something went wrong on our side. Please try again in a moment.",
    steps: {
      publish: "Publish the verification code",
      check: "Vigilo checks the code",
      verified: "Domain verified",
    },
    stepDone: "done",
    who: {
      question: "Who looks after the technical side of your website?",
      someone: "Someone else: a web agency, a developer, a friend",
      someoneHint: "Vigilo writes the message for you. You only forward it.",
      me: "I do it myself",
      meHint: "Three ways to publish the code, with step-by-step guides.",
    },
    delegate: {
      intro:
        "Send this message to the person who looks after your website. It tells them exactly what to do, in about 2 minutes. You do not need to understand it.",
      email: "Send by email",
      whatsapp: "Send on WhatsApp",
      copy: "Copy the message",
      subject: (domain: string) => `Please verify ${domain} for a Vigilo security scan`,
      message: (p: ProofMessage) =>
        `Hello,\n\nI would like to run a Vigilo security scan of ${p.domain}. To prove that the website is ours, could you do ONE of these three things? It takes about 2 minutes.\n\n1. HTML tag: paste this line inside the <head> section of the home page, then publish:\n${p.tag}\n\n2. Or a file: create a file named ${p.fileName} that contains only this code:\n${p.code}\nand put it in the main folder of the website, so that it opens at ${p.fileUrl}\n\n3. Or a DNS record: add a TXT record named ${p.dnsName} with this value:\n${p.dnsValue}\n\nThe code is valid until ${p.until}. Vigilo checks by itself: nothing else to do.\n\nThank you!`,
    },
    methodsTitle: "Choose one way to publish the code",
    methods: { meta: "HTML tag", file: "File on the website", dns: "DNS record" } as Record<ProofMethod, string>,
    methodHints: {
      meta: "The easiest: one line in the settings of your site.",
      file: "If you can upload files to your website.",
      dns: "If you manage your domain name.",
    } as Record<ProofMethod, string>,
    metaInstructions: "Paste this line inside the <head> section of your home page, then save and publish:",
    metaLabel: "Tag",
    fileInstructions:
      "Download this file and put it in the main folder of your website, the one that contains the home page. It must then open at this address:",
    download: (name: string) => `Download ${name}`,
    fileAddress: "Address",
    dnsInstructions: "Add this record to your domain's DNS zone:",
    dnsDelay: "A new record can take up to an hour to appear.",
    recordType: "Type",
    recordName: "Name",
    recordValue: "Value",
    guidesTitle: "Step-by-step guides",
    guidesFor: "Where is your website?",
    guidesNote: "Menus change from time to time: if a label is different, look for the closest one.",
    guides: {
      meta: [
        {
          name: "WordPress",
          steps: [
            "In your WordPress dashboard, open Plugins > Add New Plugin and search for “WPCode”. Install it and activate it (it is free).",
            "Open Code Snippets > Header & Footer.",
            "Paste the tag in the Header box, then click Save Changes.",
            "If your site uses a cache plugin, clear its cache.",
          ],
        },
        {
          name: "Joomla, Drupal, PrestaShop or a custom site",
          steps: [
            "Open the template (theme) of the home page in your administration or code editor.",
            "Find the line </head> and paste the tag just before it.",
            "Save and publish, then clear the cache if there is one.",
          ],
        },
      ],
      file: [
        {
          name: "Hosting panel (cPanel, hPanel, Plesk)",
          steps: [
            "Download the file with the button above.",
            "Log in to your hosting panel and open the File Manager.",
            "Open the main folder of the website: usually public_html, www, htdocs or httpdocs (the one that contains index.php or index.html).",
            "Upload the file there, without renaming it.",
            "Open the address shown above: you should see the code.",
          ],
        },
        {
          name: "FTP (FileZilla)",
          steps: [
            "Download the file with the button above.",
            "Connect to your website with your FTP details.",
            "On the server side, open the folder that contains the home page (public_html, www or htdocs).",
            "Drag the file into it, then open the address shown above to check.",
          ],
        },
      ],
      dns: [
        {
          name: "Cloudflare",
          steps: [
            "Log in to dash.cloudflare.com and select your domain.",
            "Open DNS > Records and click Add record.",
            "Type: TXT. Name: _vigilo. Content: the value shown above. Click Save.",
          ],
        },
        {
          name: "OVHcloud",
          steps: [
            "In the OVHcloud Control Panel, open Web Cloud > Domain names and select your domain.",
            "Open the DNS zone tab and click Add an entry.",
            "Choose TXT, enter _vigilo as the sub-domain and the value shown above, then confirm.",
          ],
        },
        {
          name: "GoDaddy",
          steps: [
            "Open My Products, find your domain and click DNS.",
            "Click Add New Record and choose TXT.",
            "Name: _vigilo. Value: the value shown above. Click Save.",
          ],
        },
        {
          name: "IONOS",
          steps: [
            "Open Domains & SSL, select your domain, then open DNS.",
            "Click Add record and choose TXT.",
            "Host name: _vigilo. Value: the value shown above. Click Save.",
          ],
        },
        {
          name: "Another provider",
          steps: [
            "Log in where you bought your domain name and look for “DNS zone”, “DNS records” or “Manage DNS”.",
            "Add a record of type TXT.",
            "Name (or Host): _vigilo. Some providers ask for the full name shown above instead. Value: the value shown above.",
            "Save. The record can take up to an hour to appear.",
          ],
        },
      ],
    } as Record<ProofMethod, Guide[]>,
    expires: (time: string) => `This code is valid until ${time}.`,
    waiting:
      "Waiting for the code. Vigilo checks by itself every 30 seconds. You can leave and come back later: this browser remembers the code until it is verified.",
    lastChecked: (time: string) => `Last check at ${time}: not published yet.`,
    paused: "Automatic checks are paused. Click “Check now” once the code is published.",
    verify: "Check now",
    verifying: "Checking…",
    newCode: "Get a new code",
    verified: (domain: string) => `${domain} is verified`,
    validUntil: (time: string) => `The proof is valid until ${time}.`,
    keepProof:
      "Leave the tag, the file or the record in place: it is checked again before each active scan. Remove it to withdraw your permission.",
    hosted: (platform: string) =>
      `Your website runs on ${platform}. ${platform} looks after the security of its own servers and does not allow anyone to scan them, so the active scan does not apply. The check-up above stays valid.`,
    conditionsTitle: "Before you start",
    conditions: [
      "For about 10 minutes, Vigilo sends test requests to this website with Nuclei and OWASP ZAP.",
      "Only safe checks run: no attack, no password guessing, no load test. A fragile site can still slow down, so choose a quiet moment.",
      "This is not a penetration test: a good result does not prove that the site cannot be attacked.",
      "Just before the start, the proof of ownership is checked again. Vigilo records the date, the domain, the proof and your IP address, to show who asked for the scan.",
      "You confirm that you are responsible for this website and allowed to have it tested.",
    ],
    accept: "I have read these conditions and I want to scan this website.",
    mustAccept: "Please accept the conditions first.",
    launch: "Start the active scan",
    launching: "Checking the proof…",
    runningTitle: (domain: string) => `Active scan of ${domain}`,
    runningIntro: "This takes about 10 minutes. Keep this page open: the report appears here at the end.",
    stoppedTitle: "The active scan stopped",
    retry: "Try again",
    reportTitle: "Active scan",
    reportMethod: "Active, on a verified domain. Safe checks with Nuclei and OWASP ZAP.",
    reportKept: "Nothing on our servers, except the consent record: date, domain, proof and IP address.",
    separateGrade: "This grade only covers the active scan. It is separate from the check-up grade.",
    back: "Back to the check-up",
  },
  severity: {
    critical: "Critical",
    high: "High",
    medium: "Medium",
    low: "Low",
    info: "Info",
    pass: "Pass",
    note: "Note",
  },
  platforms: {
    apache: "Apache",
    nginx: "Nginx",
    cloudflare: "Cloudflare",
    wordpress: "WordPress",
  },
  method: {
    rail: "Method",
    title: "How the check works",
    intro:
      "The check-up only looks at what any visitor's browser can see. It never tries to break in, guess passwords or send forms. The optional active scan goes further, and only for owners who proved that the domain is theirs.",
    sections: [
      {
        label: "What is checked",
        title: "The exact list",
        items: [
          "HTTPS: the site answers on a secure connection at all.",
          "Certificate: trusted by browsers, covers the domain, days before expiry.",
          "Encryption: TLS 1.0 and 1.1 refused, TLS 1.2 and 1.3 offered (rules from BSI TR-03116-4).",
          "Redirect: plain http:// addresses are sent to https://.",
          "Security headers on the home page: Strict-Transport-Security, Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy.",
          "Software versions shown in the Server and X-Powered-By headers.",
          "Sensitive files: /.git/HEAD, /.git/config, /.env, /backup.zip, /backup.sql, /database.sql, /dump.sql, /wp-config.php.bak.",
          "Email security, from public DNS: SPF, DMARC, and DKIM keys under 15 common names. The mail provider is recognised from the MX records to suggest a ready-made SPF record.",
          "Website platform: WordPress, Joomla, Drupal, PrestaShop, Shopify, Wix, Squarespace or Webflow, whether the version is visible, and whether WordPress is up to date. WordPress plugins linked by the page are compared with their latest version on wordpress.org.",
          "Privacy and legal basics in the home page HTML: fonts loaded from Google, trackers without a consent tool, a privacy policy link, an Impressum for German and Austrian sites, mentions légales for French sites.",
        ],
      },
      {
        label: "How",
        title: "Passive and polite",
        items: [
          "One request per resource, about 20 in total, at most 3 at the same time, plus about 20 public DNS queries for email records.",
          "Requests identify themselves with the User-Agent \"Vigilo\".",
          "Each request waits 10 seconds at most. At most 5 redirects are followed.",
          "For sensitive files, only the status code and the declared size are read. The content is never downloaded, shown or stored.",
          "Addresses that point to private networks are refused, including after a redirect. Each connection goes to the exact address that was checked.",
          "To know the latest WordPress version, Vigilo asks the public wordpress.org API. The answer is cached for 6 hours.",
        ],
      },
      {
        label: "Active scan",
        title: "Going further, on verified domains only",
        items: [
          "When this service offers it, an optional active scan sends test requests with two well-known open-source tools: Nuclei (known vulnerabilities, exposed files and admin pages) and the OWASP ZAP baseline (a short crawl of the site, then passive rules). It takes about 10 minutes.",
          "Only safe checks run: no denial of service, no password guessing, no fuzzing, no exploitation and no calls to outside servers. At most 20 requests per second.",
          "It only runs on a domain whose owner proved control of it, the way Google Search Console does it: an HTML tag in the home page, a file at the root of the site, or a DNS record. Vigilo can write the request for whoever runs the site, and looks for the code by itself.",
          "The proof is checked again just before each scan: removing the tag, the file or the record withdraws the permission. A proof is valid for 24 hours.",
          "Only the exact verified name is scanned: example.com does not cover shop.example.com. The tools cannot follow a redirect to another site.",
          "Each tool runs in its own short-lived, locked-down container, with limited memory and time, and is stopped at the end.",
          "Sites on Shopify, Wix, Squarespace or Webflow are not offered the active scan: it would test the platform's own servers, which their terms forbid.",
          "Results keep only the address, the parameter name and the tool's description of the problem, never content from the site. Problems the check-up already reports are not counted twice.",
        ],
      },
      {
        label: "Limits",
        title: "What this check cannot tell you",
        items: [
          "It is not a penetration test. A good grade does not mean a site cannot be attacked.",
          "Only the home page headers are read. Other pages may behave differently.",
          "Some servers answer every address with a page. HTML answers are ignored for sensitive files, which can hide a real exposure.",
          "TLS 1.0 and 1.1 can only be tested if the scanning server still supports them. If not, the report says so.",
          "Themes, your code, and plugins that hide their version or are not on wordpress.org are not checked. DKIM keys with unusual names cannot be found.",
          "Trackers and links added by JavaScript after the page loads are not seen.",
          "Legal points only look for links on the home page. They are a reminder, not legal advice.",
          "The active scan is not a penetration test either: there is no human and no exploitation. Problems that need logging in or attacking forms stay invisible.",
        ],
      },
      {
        label: "Data",
        title: "What is kept",
        items: [
          "Reports are not stored on the server. They exist only in your browser until you close the page.",
          "If you choose Remember on this device, your browser keeps a short summary of the report (date, score, grade and the names of the problems) to show your progress next time. It is never sent to Vigilo, and Forget this website removes it.",
          "To prevent abuse, the service counts checks per IP address. This count is kept in memory for 10 minutes, then forgotten.",
          "PDF files are created when you click Download and are not kept on the server. Each report carries a signature, so a modified report cannot be turned into a PDF.",
          "For each active scan, Vigilo records the date, the domain, the proof used and your IP address, to show who asked for it. Nothing else about the scan is kept.",
          "While you wait for a verification code to be published, your browser keeps it, so you can come back later. It is removed once verified or expired.",
        ],
      },
      {
        label: "Grade",
        title: "How the grade is calculated",
        items: [
          "Every site starts at 100 points. Each problem removes points: critical 40, high 20, medium 10, low 3. A warning removes half.",
          "Privacy and legal points are listed in the report but do not change the grade.",
          "The active scan is graded the same way, with a grade of its own: the check-up grade stays comparable between sites.",
        ],
      },
    ],
  },
};

export type Messages = typeof en;
