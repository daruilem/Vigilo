/**
 * Every piece of interface text lives here. To add a language, copy this file,
 * translate the values and keep the same shape (enforced by the `Messages` type).
 */
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
      { term: "Kept", text: "Nothing. The report disappears when you close the page." },
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
    keptValue: "Nothing. This report disappears when you close the page.",
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
      choose: "Publish the verification code",
      verify: "Check the code",
      verified: "Domain verified",
    },
    stepDone: "done",
    methods: { dns: "DNS record", file: "File on the website" } as Record<"dns" | "file", string>,
    methodHints: {
      dns: "If you can edit your domain's DNS zone, at your registrar or host.",
      file: "If you can upload files to your website, by FTP or in your hosting panel.",
    } as Record<"dns" | "file", string>,
    dnsInstructions: "Add this record to your domain's DNS zone:",
    dnsDelay: "A new record can take up to an hour to appear.",
    recordType: "Type",
    recordName: "Name",
    recordValue: "Value",
    fileInstructions: "Create a text file at this address, containing only the code:",
    fileAddress: "Address",
    fileContent: "Content",
    expires: (time: string) => `This code is valid until ${time}.`,
    verify: "Check now",
    verifying: "Checking…",
    newCode: "Get a new code",
    verified: (domain: string) => `${domain} is verified`,
    validUntil: (time: string) => `The proof is valid until ${time}.`,
    keepProof:
      "Leave the record or the file in place: it is checked again before each active scan. Remove it to withdraw your permission.",
    comingSoon: "The active scan itself is being built and will be available here soon.",
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
      "Vigilo only looks at what any visitor's browser can see. It never tries to break in, guess passwords or send forms.",
    sections: [
      {
        label: "What is checked",
        title: "The exact list",
        items: [
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
        ],
      },
      {
        label: "Data",
        title: "What is kept",
        items: [
          "Reports are not stored. They exist only in your browser until you close the page.",
          "To prevent abuse, the service counts checks per IP address. This count is kept in memory for 10 minutes, then forgotten.",
          "PDF files are created when you click Download and are not kept on the server. Each report carries a signature, so a modified report cannot be turned into a PDF.",
        ],
      },
      {
        label: "Grade",
        title: "How the grade is calculated",
        items: [
          "Every site starts at 100 points. Each problem removes points: critical 40, high 20, medium 10, low 3. A warning removes half.",
          "Privacy and legal points are listed in the report but do not change the grade.",
        ],
      },
    ],
  },
};

export type Messages = typeof en;
