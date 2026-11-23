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
          "A: 90 and above. B: 80 to 89. C: 65 to 79. D: 50 to 64. F: below 50.",
          "Privacy and legal points are listed in the report but do not change the grade.",
        ],
      },
    ],
  },
};

export type Messages = typeof en;
