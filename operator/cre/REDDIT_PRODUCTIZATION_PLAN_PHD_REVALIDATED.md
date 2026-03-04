# Reddit Productization Plan (PhD, Revalidated)

## Executive Summary
The existing productization direction is correct, but it was still incomplete for a professional software sale. After revalidation against stronger primary sources, the proper plan is not merely to create a separate Reddit-specific repository. The correct plan is to build a **bounded product package** with five explicit boundaries:

1. **System boundary**: define the Reddit product as its own system-of-interest.
2. **Repository boundary**: create a separate repository with only Reddit-relevant implementation.
3. **IP boundary**: classify background IP, reusable internal assets, and customer-deliverable artifacts explicitly.
4. **Supply-chain boundary**: ship dependency transparency, provenance, and integrity artifacts alongside the product.
5. **Operational boundary**: define support model, update model, approval model, and customer-facing interfaces.

This memo strengthens the earlier plan by adding delivery-model analysis, acceptance gates, procurement artifacts, provenance/attestation expectations, and a migration sequence from private R&D substrate to sellable Reddit product.

## Research Question
How should a private general-purpose visual agent R&D platform be converted into a professional Reddit-specific commercial product for advanced engineering buyers without over-disclosing unrelated research assets, implementation substrate, or internal intellectual property?

## Revalidated Conclusion
The strongest path is a **controlled product derivation** with an explicit **go-to-market packaging layer**. In practice, that means:

- Keep `concentric_study` private as the R&D/core-asset base.
- Build a separate Reddit-specific product repository.
- Deliver only a bounded Reddit product plus professional customer artifacts.
- Prefer a hosted or managed-service delivery model unless source transfer is commercially required.
- If source is delivered, accompany it with SBOM, provenance/attestation, architecture docs, interface docs, support boundaries, and explicit background-IP reservation.

## Strongest Primary Sources and Why They Matter
### 1. Architecture description must match the delivered system
ISO/IEC/IEEE 42010 requires architecture descriptions to address the stakeholders and concerns of the actual system being described. SEI's Views and Beyond reinforces that architecture documentation should organize the system through views relevant to builders, operators, and maintainers.

Implication here:
- the buyer should receive the architecture of the Reddit product, not the architecture of the broader R&D platform.

Sources:
- ISO/IEC/IEEE 42010 Architecture Descriptions: https://www.iso-architecture.org/ieee-1471/ads/
- ISO/IEC/IEEE 42010 conceptual model: https://www.iso-architecture.org/ieee-1471/cm/
- SEI Views and Beyond fact sheet (2018): https://www.sei.cmu.edu/library/views-and-beyond-the-sei-approach-for-architecture-documentation/
- SEI Documenting Software Architectures, 2nd ed.: https://www.sei.cmu.edu/library/documenting-software-architectures-views-and-beyond-second-edition/

### 2. Product-line engineering supports deriving a narrow product from a private core asset base
SEI product-line guidance defines a core asset base and requires variability to be planned and managed explicitly. That is exactly the right model for converting `concentric_study` into a Reddit-only product.

Implication here:
- `concentric_study` is a private core asset base.
- the Reddit software is a derived product with deliberate inclusion and exclusion decisions.
- handing over the whole core asset base would be a variability-control failure.

Sources:
- SEI Variability in Software Product Lines (2005): https://www.sei.cmu.edu/library/variability-in-software-product-lines/
- SEI Managing Variability in Software Architectures: https://www.sei.cmu.edu/library/managing-variability-in-software-architectures/

### 3. Buyers need interface contracts and operational constraints, not internal research sprawl
SEI interface-documentation guidance emphasizes that software interfaces should be documented both semantically and syntactically.

Implication here:
- the deliverable must expose API/CLI/webhook/admin contracts clearly.
- unrelated internals, experiments, and alternate execution paths should stay private.

Source:
- SEI Documenting Software Architecture: Documenting Interfaces: https://www.sei.cmu.edu/library/documenting-software-architecture-documenting-interfaces/

### 4. Professional software delivery requires secure development and acquisition artifacts
NIST SSDF and the generative-AI community profile establish secure development expectations. CISA's Secure by Demand and Software Acquisition guidance make clear that buyers should ask for transparency artifacts and product-security evidence.

Implication here:
- a serious deliverable is not just source code.
- it should include test evidence, dependency inventory, security notes, support boundaries, and customer-facing security/procurement artifacts.

Sources:
- NIST SP 800-218 SSDF: https://csrc.nist.gov/pubs/sp/800/218/final
- NIST SP 800-218A (2024): https://csrc.nist.gov/pubs/sp/800/218/a/final
- CISA Secure by Demand Guide (2024): https://www.cisa.gov/resources-tools/resources/secure-demand-guide
- CISA Software Acquisition Guide fact sheet (2024): https://www.cisa.gov/resources-tools/resources/software-acquisition-guide-fact-sheet
- CISA Secure by Design: https://www.cisa.gov/securebydesign
- CISA Product Security Bad Practices (2025): https://www.cisa.gov/resources-tools/resources/product-security-bad-practices

### 5. Supply-chain transparency should go beyond a plain dependency list
CISA and OpenSSF guidance show that SBOMs are useful but not sufficient by themselves; provenance and attestations improve trust in what was actually built and shipped.

Implication here:
- if you are selling to advanced engineers, include at minimum an SBOM and ideally build provenance/attestation.
- this is especially important if the customer receives source, release artifacts, or container images.

Sources:
- CISA Shared Vision of SBOM for Cybersecurity (2025): https://www.cisa.gov/resources-tools/resources/shared-vision-software-bill-materials-sbom-cybersecurity
- OpenSSF SLSA 1.0 release (2023): https://openssf.org/press-release/2023/04/19/openssf-announces-slsa-version-1-0-release/
- OpenSSF artifact attestations overview (2024): https://openssf.org/blog/2024/05/24/introducing-artifact-attestations-now-in-public-beta/
- OpenSSF SBOM and attestations deep dive (2024): https://openssf.org/blog/2024/06/26/a-deep-dive-into-sbomit-and-attestations/

### 6. Background IP and deliverable IP must be separated formally
Official IP guidance distinguishes background/existing IP from foreground/new IP, and licensing from assignment.

Implication here:
- `concentric_study` should be treated as background IP.
- the Reddit product should be licensed or transferred as a bounded deliverable.
- the boundary should be explicit in the commercial package.

Sources:
- GOV.UK IP Rights Guidance Note: https://www.gov.uk/government/publications/the-digital-data-and-technology-playbook/intellectual-property-rights-guidance-note-html
- WIPO Technology Transfer Agreements: https://www.wipo.int/en/web/technology-transfer/agreements

## What Needed Enhancement in the Earlier Plan
The earlier plan was right on scope separation, but it needed four upgrades.

### Upgrade 1: delivery-model selection
The earlier plan assumed a source-deliverable orientation too early. That is risky. The first decision should be whether the Reddit product is delivered as:
- hosted service
- managed deployment
- source-available product
- source-transfer/custom codebase

For protection of IP and operational quality, the default recommendation is:
1. hosted service if feasible
2. managed deployment if customer needs private environment
3. source delivery only if commercially necessary

### Upgrade 2: provenance and build integrity
The earlier plan required a dependency manifest and SBOM, but not build provenance or attestations. That is now below professional expectation for advanced buyers.

Add:
- SBOM
- signed release artifacts or checksums
- provenance/attestation where build tooling supports it

### Upgrade 3: acceptance and support gates
The earlier plan described what to deliver but not what must be true before delivery.

Add explicit release gates:
- Reddit-only repo boundary validated
- no confidential/internal docs present
- no unrelated experiments present
- passing tests
- deployment reproducibility check
- security review checklist completed
- support boundary defined

### Upgrade 4: customer procurement packet
The earlier plan described engineering artifacts but not the buying packet.

Add a lightweight procurement bundle:
- product overview
- architecture summary
- interface specification
- deployment and operations guide
- security posture summary
- dependency/SBOM package
- support and update policy
- known limitations

## Revalidated PhD Plan
### Phase 1: Define the Reddit product as a standalone system-of-interest
Create a one-page scope statement with:
- mission
- supported workflows
- excluded workflows
- actors and stakeholders
- trust boundary
- operating environment
- approval and moderation boundary

Decision rule:
If a capability is not required for Reddit content planning, drafting, approval, posting, evidence capture, or analytics, it does not belong in the customer product.

### Phase 2: Perform an explicit asset triage
Produce a three-column inventory:
1. **Background IP retained privately**
2. **Reusable internal asset candidates**
3. **Customer-deliverable artifacts**

Examples of background IP to retain:
- general-purpose agent research docs
- unrelated art/canvas automation
- historical runs
- old experimental stacks
- broad multi-site exploration assets

Examples of customer-deliverable artifacts:
- Reddit-specific browser workflow modules
- Reddit posting policy checks
- approval flow
- product configs
- deployment files
- product docs
- tests and evidence specific to Reddit workflows

### Phase 3: Choose the delivery model before copying code
Use a decision matrix:
- **Hosted**: best IP protection, best operational control, weakest customer code access
- **Managed deployment**: good control, customer-hosted environment, moderate operational complexity
- **Source-available licensed product**: higher transparency, higher IP exposure
- **Source-transfer/custom repo**: highest customer autonomy, highest IP leakage risk

Default professional recommendation:
- start with hosted or managed deployment unless the deal explicitly requires source transfer

### Phase 4: Create a new repository as a product, not a filtered snapshot
The new repository should have:
- new identity
- new README
- Reddit-only code surface
- clean git history if possible
- no accidental carryover from internal experiments

Recommended structure:
- `reddit_publisher/`
- `src/`
- `docs/`
- `tests/`
- `configs/`
- `scripts/`
- `artifacts/`
- `sbom/`
- `README.md`
- `ARCHITECTURE.md`
- `INTERFACES.md`
- `OPERATIONS.md`
- `SECURITY.md`
- `CHANGELOG.md`
- `SUPPORT.md`

### Phase 5: Write the customer-facing architecture package before porting code
Minimum docs:
- **Context view**
- **Module view**
- **Runtime/workflow view**
- **Deployment view**
- **Interface specification**
- **Config and variability guide**
- **Known limitations**

This should be Reddit-only and customer-facing.

### Phase 6: Port or reimplement only the Reddit-relevant components
Port selectively from the internal platform:
- browser/window capture patterns
- tracing/evidence patterns
- approval-gated execution patterns
- verification patterns
- site-knowledge schema patterns

Do not port blindly:
- unrelated site logic
- art-task flows
- dead code and legacy stacks
- internal-only research scaffolding not required by the Reddit product

### Phase 7: Build the professional release packet
Minimum release packet:
- product code
- tests
- deployment guide
- operator guide
- architecture package
- interface specification
- dependency manifest
- SBOM
- release notes
- support policy
- known limitations

Recommended additions:
- provenance/attestation
- signed release checksums
- threat model summary
- moderation/policy guardrail statement

### Phase 8: Add acceptance gates before any customer handoff
A release is not ready unless all gates pass.

#### Engineering gates
- all Reddit product tests pass
- build is reproducible
- deployment instructions work from a clean environment
- tracing/evidence outputs are sane

#### Boundary gates
- no unrelated modules present
- no private R&D docs shipped
- no old run artifacts shipped
- no hidden credentials/secrets/config leaks

#### Security gates
- dependency review completed
- SBOM generated
- security posture summary updated
- logging and auth assumptions documented

#### Commercial gates
- support boundary written
- update and patching policy written
- background IP reservation reviewed
- deliverable list finalized

## What the Customer Should Receive
### If hosted or managed deployment
Provide:
- architecture summary
- interface docs
- operator/admin docs
- security and support packet
- evidence of testing and release provenance

Do not provide by default:
- internal source for unrelated capabilities
- private research artifacts
- internal experimental infrastructure

### If source delivery is required
Provide only:
- Reddit-only repository
- Reddit-only docs
- Reddit-only tests
- dependency and supply-chain artifacts
- explicit license/support terms

Do not provide:
- `concentric_study`
- broad internal run corpus
- multi-site/private experimentation assets

## Recommended Customer Procurement Packet
The minimum customer-facing packet should contain:
- Product Overview
- Supported Use Cases and Exclusions
- Architecture Summary
- Interfaces and Configuration Guide
- Deployment Guide
- Security Summary
- SBOM
- Provenance/Integrity Notes
- Support and Update Policy
- Known Limitations and Assumptions

## Anti-Patterns to Avoid
Do not:
- hand over the whole research repo
- ship a repo that still visibly looks like an internal lab carve-out
- rely on folder deletion as your only separation strategy
- mix client product docs with internal research memos
- promise source transfer if you really want a product/license model
- ship an SBOM without basic release integrity information
- leave support and patching assumptions implicit

## Final Recommendation
The enhanced plan is:
1. Treat `concentric_study` as private background IP and R&D substrate.
2. Define the Reddit product as a separate system-of-interest.
3. Prefer hosted or managed delivery unless source transfer is required.
4. Create a fresh Reddit-only repository.
5. Port only the smallest reusable subset from the internal platform.
6. Ship professional engineering, security, and procurement artifacts with the product.
7. Make boundaries explicit: architecture, repository, IP, supply chain, and operations.

That is the strongest PhD-level path and the most credible professional path.
