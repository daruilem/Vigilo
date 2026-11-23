import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { Label, Section, SectionNumber } from "@/components/Section";
import { getMessages, isLocale } from "@/i18n";
import { sectionNumber } from "@/lib/report";

export async function generateMetadata({ params }: PageProps<"/[lang]/method">): Promise<Metadata> {
  const { lang } = await params;
  return isLocale(lang) ? { title: getMessages(lang).meta.methodTitle } : {};
}

export default async function MethodPage({ params }: PageProps<"/[lang]/method">) {
  const { lang } = await params;
  if (!isLocale(lang)) notFound();
  const t = getMessages(lang);
  return (
    <article aria-labelledby="method-title">
      <Section first rail={<Label>{t.method.rail}</Label>}>
        <h1
          id="method-title"
          className="font-serif text-[32px] leading-10 font-semibold md:text-[40px] md:leading-[48px]"
        >
          {t.method.title}
        </h1>
        <p className="mt-3 max-w-[640px]">{t.method.intro}</p>
      </Section>

      {t.method.sections.map((section, index) => {
        const headingId = `method-${index}`;
        return (
          <Section
            key={section.label}
            labelledBy={headingId}
            rail={
              <>
                <SectionNumber value={sectionNumber(index)} />
                <Label>{section.label}</Label>
              </>
            }
          >
            <div className="max-w-[760px]">
              <h2 id={headingId} className="font-serif text-2xl leading-8 font-semibold md:text-[28px] md:leading-9">
                {section.title}
              </h2>
              <ul className="mt-3 border-t border-ink">
                {section.items.map((item) => (
                  <li key={item} className="border-b border-rule py-3">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </Section>
        );
      })}
    </article>
  );
}
