# Welqin — Vocabulaire métier et codes de référence

Welqin est une plateforme B2B de gestion de transactions de propriété intellectuelle (PI) basée sur la norme **AFNOR NF X50-276**. Ce document fournit le vocabulaire canonique et les codes à utiliser dans les synthèses de réunions.

---

## Acteurs et rôles

| Terme | Définition |
|---|---|
| **Agent** | Toute organisation enregistrée sur Welqin (cabinet PI, entreprise, office) |
| **Primary Agent** | Agent émetteur d'une transaction (rang 1) |
| **Secondary Agent** | Agent récepteur / exécutant (rang 2, 3…) |
| **IP Owner / Titulaire** | Propriétaire des droits PI |
| **IP Firm / Cabinet PI** | Cabinet d'avocats ou de conseil en PI |
| **PTO** | Patent & Trademark Office — office national ou régional |
| **Foreign Filing Firm** | Cabinet de dépôt étranger (rang 2) |
| **Foreign Prosecution Firm** | Cabinet de poursuite de procédure à l'étranger (rang 3) |
| **Service Provider** | Prestataire (traduction, recherche, formalités…) |
| **Cooperation** | Relation B2B formalisée entre deux agents sur Welqin |

---

## Workflow PI — Termes du cycle de vie

| Terme | Sens |
|---|---|
| **Filing Instruction** | Instruction de dépôt envoyée au cabinet étranger |
| **Hand-Over Confirmation** | Accusé de prise en charge par le Secondary Agent |
| **Filing Report** | Rapport de dépôt avec numéro et date officiels |
| **Formal OA** | Office Action formelle (examen de forme) |
| **Substantive OA** | Office Action substantielle (examen au fond) |
| **OA Response** | Réponse à une Office Action |
| **Grant Decision** | Décision de délivrance du titre |
| **Validation** | Validation nationale d'un titre EP ou PCT |
| **Annuity / Renewal** | Renouvellement ou annuité de maintien en vigueur |
| **Recordal** | Inscription modificative au registre |
| **Missing Details** | Demande de précisions complémentaires |
| **Completion** | Clôture d'un dossier de dépôt étranger |

**Codes d'interaction AFNOR** : `INS` (Instruction) · `INF` (Information) · `REQ` (Request) · `RPT` (Report) · `CNF` (Confirmation) · `RJT` (Rejection) · `CLS` (Closure)

---

## Comptabilité

**Natures de document** : `INVOICE_DEBIT` · `INVOICE_CREDIT` · `PROVISION_DEBIT` · `PROFORMA` · `QUOTATION` · `PURCHASE_ORDER` · `DISBURSEMENT`

**Types de frais** : `PROFESSIONALFEES` · `OFFICIALFEES` · `EXPENSES`

**Codes de prestation** : `ATTORNEY` · `PARALEGAL` · `TRANSLATION` · `SEARCH` · `DRAWING` · `FORMALITY` · `TRANSMISSION` · `RENEWAL` · `FILING`

**Unités** : `HOURS` · `PAGES` · `WORDS` · `CLAIMS_TOTAL` · `CLAIMS_INDEP` · `CLASSES` · `DRAWINGS` · `DAYS` · `FLAT_FEE`

---

## Intégrations externes

| Système | Contexte |
|---|---|
| **LegalTracker** | Legal Spend Management — Agent ↔ Company/Firm, Transaction ↔ Matter |
| **Pennylane** | Export comptable des factures et débours |
| **Chorus Pro / PISTE** | Facturation électronique B2G (France) |
| **WIPO PATENTSCOPE** | Enrichissement de dossiers PCT |
| **Madrid Monitor** | Suivi des marques internationales WIPO |
| **Peppol BIS 3.0** | Standard européen de facturation B2B |
| **LEDES 1998b/bi** | Facturation électronique cabinets d'avocats |
| **Factur-X / ZUGFeRD** | Facture mixte PDF+XML (France/Allemagne) |
| **UTBMS** | Codes de tâches et activités juridiques |

---

## Acronymes

| Sigle | Développé |
|---|---|
| PI / IP | Propriété Intellectuelle / Intellectual Property |
| OEB / EPO | Office Européen des Brevets |
| EUIPO | Office de l'UE pour la propriété intellectuelle |
| WIPO / OMPI | Organisation Mondiale de la Propriété Intellectuelle |
| INPI | Institut National de la Propriété Industrielle (France) |
| PTO | Patent & Trademark Office (générique) |
| PCT | Patent Cooperation Treaty |
| OA | Office Action |
| LSM | Legal Spend Management |
| IPMS | IP Management System |
| MCP | Model Context Protocol |
