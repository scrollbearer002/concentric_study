# Reddit Productization Plan (PhD)

## Executive Summary
The correct way to turn the current internal R&D system into a sellable Reddit-specific product is **not** to hand over the whole `concentric_study` repository and it is **not** to “hide parts informally.”

The correct path is to treat this as a **product-line derivation and controlled technology transfer problem**:
- maintain `concentric_study` as the private research/core-asset base
- define a narrow Reddit product boundary
- derive a separate customer-facing product from that base
- document only the views, interfaces, and evidence relevant to the Reddit product
- separate **background IP** from **foreground/deliverable IP** explicitly
- package the delivered product with secure-software and supply-chain artifacts appropriate for professional software buyers

This conclusion is grounded in software product-line engineering, architecture-documentation standards, secure software delivery guidance, and official IP transfer/licensing guidance.

## Research Question
How should an internal general-purpose agent R&D platform be converted into a professional, Reddit-specific commercial software product without unnecessarily disclosing the full internal platform?

## Main Conclusion
The right answer is a **three-boundary strategy**:
1. **Architecture boundary**: define a Reddit-only system of interest with explicit stakeholders and concerns.
2. **Repository boundary**: create a separate repository/product package containing only Reddit-relevant modules, docs, configs, tests, and artifacts.
3. **IP and delivery boundary**: keep the internal platform as background IP and provide the customer either a license or a tightly scoped deliverable package for the derived product.

## Authoritative Research Basis
### 1. Architecture must be documented for the specific system being delivered
- ISO/IEC/IEEE 42010 says an architecture description is the work product used to express an architecture and that it must identify stakeholders and concerns.
- It also requires that views and viewpoints cover those concerns.
- SEI's *Views and Beyond* says architecture must be captured in a form others can build, use, and maintain.

This means the customer should receive the architecture description of the **Reddit product**, not the architecture of the entire research lab.

Sources:
- ISO/IEC/IEEE 42010 Architecture Descriptions: https://www.iso-architecture.org/ieee-1471/ads/
- ISO/IEC/IEEE 42010 conceptual model: https://www.iso-architecture.org/ieee-1471/cm/
- SEI *Documenting Software Architectures: Views and Beyond, 2nd Edition*: https://www.sei.cmu.edu/library/documenting-software-architectures-views-and-beyond-second-edition/

### 2. Product-line engineering supports deriving a narrow product from a larger core asset base
SEI product-line guidance defines products as being built from a **core asset base** and stresses that variability must be explicitly planned and managed.

Applied here:
- `concentric_study` is the private core asset base.
- The Reddit product is a derived product with a deliberately chosen subset of assets and explicit variability decisions.
- Delivering the whole core asset base to one customer is exactly the kind of variability/control failure that product-line discipline is meant to avoid.

Sources:
- SEI *Variability in Software Product Lines*: https://www.sei.cmu.edu/library/variability-in-software-product-lines/
- SEI *Managing Variability in Software Architectures*: https://www.sei.cmu.edu/library/managing-variability-in-software-architectures/

### 3. Interfaces should be documented explicitly, because the customer needs the contract, not the whole internals
SEI’s interface-documentation guidance says interfaces to software elements should be documented with both semantic and syntactic information.

Applied here:
- the customer needs a clean API/CLI/webhook/admin interface contract for the Reddit product
- they do not need the full internal internals of unrelated Excalidraw/Kleki/legacy experimentation paths

Source:
- SEI *Documenting Software Architecture: Documenting Interfaces*: https://www.sei.cmu.edu/library/documenting-software-architecture-documenting-interfaces/

### 4. Secure software delivery requires more than source code handoff
NIST SSDF recommends secure software development practices to reduce released vulnerabilities and mitigate exploitation impacts.
NIST 800-218A extends that mindset to AI systems and AI-enabled software producers and acquirers.
CISA’s software-acquisition and secure-by-demand guidance emphasize that buyers should obtain transparency artifacts such as SBOMs and security information from suppliers.

Applied here:
- the deliverable should include a professional software package: tested code, dependency inventory, operational docs, security notes, and support boundaries
- this is better than handing over a research repo because it gives the customer the software they need while reducing accidental disclosure and supply-chain confusion

Sources:
- NIST SP 800-218 SSDF: https://csrc.nist.gov/pubs/sp/800/218/final
- NIST SP 800-218A: https://csrc.nist.gov/pubs/sp/800/218/a/final
- CISA SBOM overview: https://www.cisa.gov/sbom
- CISA Software Acquisition Guide fact sheet: https://www.cisa.gov/resources-tools/resources/software-acquisition-guide-fact-sheet
- CISA Secure by Demand guide: https://www.cisa.gov/resources-tools/resources/secure-demand-guide

### 5. Background IP and deliverable IP should be separated explicitly
Official UK government IP guidance distinguishes:
- **Existing / Background IP**: work created before or independently of the contract
- **New / Foreground IP**: work created under the contract
It also explains that licensing is often preferable to outright ownership for protecting both parties’ interests.
WIPO explains the difference between licensing and assignment and emphasizes confidentiality and clear treatment of background IP in collaboration/transfer agreements.

Applied here:
- `concentric_study` should be treated as **background IP**
- the Reddit product package can be either:
  - licensed as a product, or
  - transferred as a scoped codebase/deliverable
- do not blur that boundary informally

Sources:
- GOV.UK IP Rights Guidance Note: https://www.gov.uk/government/publications/the-digital-data-and-technology-playbook/intellectual-property-rights-guidance-note-html
- WIPO Technology Transfer Agreements: https://www.wipo.int/en/web/technology-transfer/agreements

## Practical PhD Plan
### Phase 1: Define the system-of-interest
Create a one-page architecture scope statement for the Reddit product only.

Required sections:
- product mission
- target users
- supported Reddit workflows
- explicit exclusions
- operational environment
- security and approval boundary

The key rule:
- anything not required for Reddit publishing, monitoring, moderation-safe drafting, or evidence capture is out of scope for the customer product

### Phase 2: Identify background IP vs deliverable surface
Create a formal asset inventory with three buckets:
1. **background IP retained privately**
2. **candidate reusable assets**
3. **customer-deliverable assets**

For example:
- keep private: unrelated site automation, broad research memos, general experiments, art-task logic, legacy demo scripts, full run corpus
- reusable but selectively packaged: window capture, tracing, verification patterns, site knowledge schema, safe execution contracts
- deliverable: Reddit-specific adapters, product docs, deployment config, tests, operational dashboards, evidence logging relevant to Reddit

### Phase 3: Create a separate repository, not a filtered view of the old one
Do **not** give the customer the main repo with folders removed.

Instead:
- create a new repository with a new product identity
- copy or reimplement only the Reddit-relevant modules
- avoid carrying over unrelated git history, experimental artifacts, and research clutter
- remove internal docs that reveal the broader R&D program

This is an engineering inference from the product-line and IP guidance: the delivered repo should be a product artifact, not a lab snapshot.

### Phase 4: Build a Reddit-specific architecture package
Using ISO 42010 and SEI Views and Beyond, prepare only the views the customer needs.

Recommended architecture package:
- **Context view**: product boundary, external systems, data flows
- **Module view**: core Reddit posting subsystems
- **Runtime/workflow view**: ingestion -> drafting -> approval -> posting -> evidence -> analytics
- **Deployment/operations view**: where it runs, secrets, queues, logs
- **Interface guide**: APIs, admin UI, schedulers, environment variables, webhooks
- **Variability guide**: what can be configured per customer
- **Known issues / limitations**: current boundaries and risks

### Phase 5: Package only the professional delivery artifacts
Minimum professional delivery package:
- source code for the Reddit product only
- README and operator guide
- architecture document
- interface specification
- deployment instructions
- test suite
- dependency manifest
- SBOM
- security notes / threat assumptions
- changelog / versioning policy
- support boundary
- sample configuration and environment template

Optional:
- VEX / vulnerability notes
- benchmark/evidence report for the Reddit workflow only

### Phase 6: Add contract-safe boundaries
Not legal advice, but the engineering plan should anticipate contract structure.

At minimum, prepare to define:
- what remains your **background IP**
- what is being delivered as product code
- whether they receive source, binaries, hosted service, or a license
- whether they can modify it
- what maintenance/support they get
- what confidential information is excluded

This is where counsel should review the final commercial terms.

### Phase 7: Build customer trust through narrow transparency, not total disclosure
Advanced engineers do not need your entire lab to trust the product.
They need:
- a clean architecture
- clear interfaces
- reproducible deployment
- credible tests
- dependency transparency
- operational evidence
- supportable boundaries

That is the professional standard.

## What You Should Deliver
Deliver:
- a Reddit-only product repo
- Reddit-only architecture docs
- Reddit-only tests and evidence
- productized dependency and security artifacts
- a clear API/operating model

Do not deliver:
- the full `concentric_study` repo
- unrelated experiments and historical runs
- broad internal research memos unless they directly support the Reddit product
- unrelated automation capabilities
- legacy stacks unless the Reddit product actually uses them

## Suggested Deliverable Structure
Recommended separate repository shape:
- `reddit_publisher/`
- `src/`
- `docs/`
- `tests/`
- `configs/`
- `artifacts/`
- `sbom/`
- `scripts/`
- `README.md`
- `ARCHITECTURE.md`
- `INTERFACES.md`
- `SECURITY.md`
- `OPERATIONS.md`
- `CHANGELOG.md`

## Immediate Next Steps
1. Draft the product mission and exclusions for the Reddit product.
2. Build a background-IP vs deliverable-IP inventory from the current repo.
3. Define the minimal reusable module set.
4. Create the new repository with no accidental carryover.
5. Write the Reddit-only architecture and interface docs before copying code.
6. Only then start porting or rewriting modules.

## Bottom Line
The professional move is not concealment.
It is **controlled productization**.

You should treat `concentric_study` as the private research platform and create a separate, Reddit-specific product derived from it using explicit architecture, variability, IP, interface, and delivery boundaries.

That is the PhD-level path and the commercially credible path.
