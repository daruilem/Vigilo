"""Fixed text of the PDF report in each language (the findings are translated by i18n)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Labels:
    title: str
    checked_on: str
    method: str
    method_value: str
    hosting: str
    grade: str
    issues: Callable[[int], str]
    severity: dict[str, str]
    not_graded: str
    observed: str
    why: str
    fix: Callable[[str], str]
    fix_fallback: str
    then: str
    passed: Callable[[int], str]
    not_checked: Callable[[int], str]
    not_checked_intro: str
    all_clear: str
    footer: str
    page: Callable[[int], str]
    scale_title: str
    scale_intro: str
    meanings: dict[str, str]
    points: str
    this_site: str
    how_calculated: str
    your_score: Callable[[int], str]


def _en_plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many.format(n=n)


def _ar_count(n: int, one: str, two: str, few: str, many: str) -> str:
    if n == 1:
        return one
    if n == 2:
        return two
    return (few if 3 <= n <= 10 else many).format(n=n)


LABELS: dict[str, Labels] = {
    "en": Labels(
        title="Security check-up",
        checked_on="Checked on",
        method="Method",
        method_value="Passive. One request per resource. No attack tested.",
        hosting="Fixes shown for",
        grade="GRADE",
        issues=lambda n: (
            "Nothing to fix" if n == 0 else _en_plural(n, "1 issue to fix", "{n} issues to fix")
        ),
        severity={
            "critical": "CRITICAL",
            "high": "HIGH",
            "medium": "MEDIUM",
            "low": "LOW",
            "pass": "PASS",
            "note": "NOTE",
        },
        not_graded="Not graded",
        observed="OBSERVED",
        why="WHY IT MATTERS",
        fix=lambda p: f"HOW TO FIX IT ({p})",
        fix_fallback="HOW TO FIX IT",
        then="Then:",
        passed=lambda n: _en_plural(n, "1 check passed", "{n} checks passed"),
        not_checked=lambda n: _en_plural(n, "1 check could not run", "{n} checks could not run"),
        not_checked_intro="These results are missing, so the grade may be too optimistic.",
        all_clear="No problem was found. Keep your software up to date and check again in a few months.",
        footer="Vigilo · passive security check-up · this report was not stored",
        page=lambda n: f"Page {n}",
        scale_title="What the grade means",
        scale_intro="The grade sums up the security problems found on the site, from A (best) to F (worst).",
        meanings={
            "A": "Very good. Only small details to improve.",
            "B": "Good. A few points to fix when you have time.",
            "C": "Fair. Several weaknesses: plan the fixes in the coming weeks.",
            "D": "Weak. Serious weaknesses: start with the most severe points now.",
            "F": "Poor. Visitors or data are at real risk: act right away.",
        },
        points="points",
        this_site="This site",
        how_calculated="Every site starts with 100 points. Each problem removes points according to its severity: critical 40, high 20, medium 10, low 3. A warning removes half. Legal points do not change the grade.",
        your_score=lambda s: f"This site scored {s} points out of 100.",
    ),
    "fr": Labels(
        title="Bilan de sécurité",
        checked_on="Analysé le",
        method="Méthode",
        method_value="Passive. Une requête par ressource. Aucune attaque testée.",
        hosting="Corrections affichées pour",
        grade="NOTE",
        issues=lambda n: (
            "Rien à corriger"
            if n == 0
            else _en_plural(n, "1 point à corriger", "{n} points à corriger")
        ),
        severity={
            "critical": "CRITIQUE",
            "high": "ÉLEVÉ",
            "medium": "MOYEN",
            "low": "FAIBLE",
            "pass": "CONFORME",
            "note": "REMARQUE",
        },
        not_graded="Non noté",
        observed="CONSTATÉ",
        why="POURQUOI C'EST IMPORTANT",
        fix=lambda p: f"COMMENT CORRIGER ({p})",
        fix_fallback="COMMENT CORRIGER",
        then="Ensuite :",
        passed=lambda n: _en_plural(n, "1 vérification réussie", "{n} vérifications réussies"),
        not_checked=lambda n: _en_plural(
            n, "1 vérification n'a pas pu être faite", "{n} vérifications n'ont pas pu être faites"
        ),
        not_checked_intro="Ces résultats manquent, la note est donc peut-être trop optimiste.",
        all_clear="Aucun problème trouvé. Gardez vos logiciels à jour et relancez une analyse dans quelques mois.",
        footer="Vigilo · bilan de sécurité passif · ce rapport n'a pas été conservé",
        page=lambda n: f"Page {n}",
        scale_title="Ce que signifie la note",
        scale_intro="La note résume les problèmes de sécurité trouvés sur le site, de A (la meilleure) à F (la moins bonne).",
        meanings={
            "A": "Très bien. Seuls quelques détails à améliorer.",
            "B": "Bien. Quelques points à corriger quand vous avez le temps.",
            "C": "Moyen. Plusieurs faiblesses : prévoyez les corrections dans les semaines qui viennent.",
            "D": "Faible. Des faiblesses sérieuses : commencez dès maintenant par les points les plus graves.",
            "F": "Mauvais. Les visiteurs ou les données sont réellement exposés : agissez tout de suite.",
        },
        points="points",
        this_site="Ce site",
        how_calculated="Chaque site part de 100 points. Chaque problème retire des points selon sa gravité : critique 40, élevé 20, moyen 10, faible 3. Un avertissement en retire la moitié. Les points juridiques ne changent pas la note.",
        your_score=lambda s: f"Ce site a obtenu {s} points sur 100.",
    ),
    "de": Labels(
        title="Sicherheitscheck",
        checked_on="Geprüft am",
        method="Methode",
        method_value="Passiv. Eine Anfrage pro Ressource. Kein Angriff getestet.",
        hosting="Korrekturen für",
        grade="NOTE",
        issues=lambda n: (
            "Nichts zu beheben"
            if n == 0
            else _en_plural(n, "1 Punkt zu beheben", "{n} Punkte zu beheben")
        ),
        severity={
            "critical": "KRITISCH",
            "high": "HOCH",
            "medium": "MITTEL",
            "low": "NIEDRIG",
            "pass": "BESTANDEN",
            "note": "HINWEIS",
        },
        not_graded="Ohne Wertung",
        observed="FESTGESTELLT",
        why="WARUM DAS WICHTIG IST",
        fix=lambda p: f"SO BEHEBEN SIE ES ({p})",
        fix_fallback="SO BEHEBEN SIE ES",
        then="Danach:",
        passed=lambda n: _en_plural(n, "1 Prüfung bestanden", "{n} Prüfungen bestanden"),
        not_checked=lambda n: _en_plural(
            n, "1 Prüfung konnte nicht laufen", "{n} Prüfungen konnten nicht laufen"
        ),
        not_checked_intro="Diese Ergebnisse fehlen, die Note ist daher vielleicht zu optimistisch.",
        all_clear="Kein Problem gefunden. Halten Sie Ihre Software aktuell und prüfen Sie in einigen Monaten erneut.",
        footer="Vigilo · passiver Sicherheitscheck · dieser Bericht wurde nicht gespeichert",
        page=lambda n: f"Seite {n}",
        scale_title="Was die Note bedeutet",
        scale_intro="Die Note fasst die gefundenen Sicherheitsprobleme zusammen, von A (am besten) bis F (am schlechtesten).",
        meanings={
            "A": "Sehr gut. Nur kleine Details zu verbessern.",
            "B": "Gut. Einige Punkte, die Sie bei Gelegenheit beheben sollten.",
            "C": "Befriedigend. Mehrere Schwächen: Planen Sie die Korrekturen in den nächsten Wochen.",
            "D": "Schwach. Ernste Schwächen: Beginnen Sie jetzt mit den schwerwiegendsten Punkten.",
            "F": "Mangelhaft. Besucher oder Daten sind ernsthaft gefährdet: Handeln Sie sofort.",
        },
        points="Punkte",
        this_site="Diese Website",
        how_calculated="Jede Website startet mit 100 Punkten. Jedes Problem zieht je nach Schwere Punkte ab: kritisch 40, hoch 20, mittel 10, niedrig 3. Eine Warnung zieht die Hälfte ab. Rechtliche Punkte ändern die Note nicht.",
        your_score=lambda s: f"Diese Website hat {s} von 100 Punkten erreicht.",
    ),
    "ar": Labels(
        title="الفحص الأمني",
        checked_on="تاريخ الفحص",
        method="المنهجية",
        method_value="سلبي. طلب واحد لكل مورد. لم يُختبر أي هجوم.",
        hosting="الإصلاحات المعروضة لـ",
        grade="التقييم",
        issues=lambda n: (
            "لا شيء يحتاج إلى إصلاح"
            if n == 0
            else _ar_count(
                n,
                "مشكلة واحدة تحتاج إلى إصلاح",
                "مشكلتان تحتاجان إلى إصلاح",
                "{n} مشكلات تحتاج إلى إصلاح",
                "{n} مشكلة تحتاج إلى إصلاح",
            )
        ),
        severity={
            "critical": "حرِج",
            "high": "مرتفع",
            "medium": "متوسط",
            "low": "منخفض",
            "pass": "ناجح",
            "note": "ملاحظة",
        },
        not_graded="غير مُقيَّم",
        observed="ما تم رصده",
        why="لماذا يهم ذلك",
        fix=lambda p: f"طريقة الإصلاح ({p})",
        fix_fallback="طريقة الإصلاح",
        then="بعد ذلك:",
        passed=lambda n: _ar_count(
            n, "فحص واحد ناجح", "فحصان ناجحان", "{n} فحوص ناجحة", "{n} فحصًا ناجحًا"
        ),
        not_checked=lambda n: _ar_count(
            n,
            "تعذّر إجراء فحص واحد",
            "تعذّر إجراء فحصين",
            "تعذّر إجراء {n} فحوص",
            "تعذّر إجراء {n} فحصًا",
        ),
        not_checked_intro="هذه النتائج مفقودة، لذا قد يكون التقييم متفائلًا أكثر من اللازم.",
        all_clear="لم يُعثر على أي مشكلة. حافظ على تحديث برامجك وأعد الفحص بعد بضعة أشهر.",
        footer="Vigilo · فحص أمني سلبي · لم يُحفظ هذا التقرير",
        page=lambda n: f"صفحة {n}",
        scale_title="ماذا يعني التقييم",
        scale_intro="يلخّص التقييم مشاكل الأمان التي عُثر عليها في الموقع، من A (الأفضل) إلى F (الأسوأ).",
        meanings={
            "A": "ممتاز. لم يتبقَّ سوى تفاصيل صغيرة للتحسين.",
            "B": "جيد. بعض النقاط التي يمكن إصلاحها عندما يتسنى لك الوقت.",
            "C": "مقبول. عدة نقاط ضعف: خطّط لإصلاحها خلال الأسابيع القادمة.",
            "D": "ضعيف. نقاط ضعف خطيرة: ابدأ الآن بأخطر النقاط.",
            "F": "سيئ. الزوار أو البيانات معرّضون لخطر حقيقي: تصرّف فورًا.",
        },
        points="نقطة",
        this_site="هذا الموقع",
        how_calculated="يبدأ كل موقع بـ 100 نقطة، وكل مشكلة تُنقص نقاطًا حسب خطورتها: حرِجة 40، مرتفعة 20، متوسطة 10، منخفضة 3. والتحذير يُنقص النصف. النقاط القانونية لا تغيّر التقييم.",
        your_score=lambda s: f"حصل هذا الموقع على {s} نقطة من 100.",
    ),
}

PLATFORM_NAMES = {
    "apache": "Apache",
    "nginx": "Nginx",
    "cloudflare": "Cloudflare",
    "wordpress": "WordPress",
}
DATE_FORMATS = {
    "en": "%d %b %Y, %H:%M UTC",
    "fr": "%d/%m/%Y, %H:%M UTC",
    "de": "%d.%m.%Y, %H:%M UTC",
    "ar": "%Y-%m-%d, %H:%M UTC",
}
