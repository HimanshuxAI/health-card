---
title: "Success Story: ABHA Health Card"
---

# SUCCESS STORY OF PROJECT

This success story describes the ABHA Health Card project completed by Group SY1512, School of Computing, MIT-ADT University. The project delivers an emergency health card prototype that combines secure QR retrieval, FHIR interoperability, claims synchronization, and emergency notification.

## The Customer

The customer is the project evaluation committee and demonstration users at MIT-ADT University, with target users in hospital emergency and billing workflows. The system is designed for patients who need a readable emergency profile, hospitals that need FHIR-based records and claims, and administrators who need audit visibility.

## The Challenge

Emergency care depends on rapidly knowing critical patient facts, but longitudinal records and billing workflows are often disconnected. Existing systems may expose too much information in QR codes or require patient interaction during an emergency. Claims are often prepared manually from proprietary hospital systems. The challenge was to build an integrated prototype that protects emergency data, supports standardized clinical records, and automates claims synchronization without depending on live national gateways.

## The Solution

The solution is a microservice-based ABHA Health Card prototype. A patient saves an emergency profile that is sealed with AES-128-GCM and HMAC-SHA256. The patient receives a rotating QR token that contains no medical data. A responder resolves the token to a minimum emergency profile without authentication. Hospital users create FHIR R4 records and itemized bills. The NHCX service converts bills to FHIR Claim resources and applies an explicit state machine. SOS alerts use WebSocket and SMTP fallback.

## Importance of Resource Management

Resource management ensured that five backend services, a frontend, a gateway, and documentation were delivered within the academic timeline. Each service owned one database and one bounded context. This reduced coupling and allowed parallel development. Tests and seed data were maintained alongside implementation, which prevented late integration failures.

## Resource Planning

The project was planned in phases: requirements, design, identity service, records service, ABDM and FHIR service, NHCX service, SOS service, frontend, integration, testing, and documentation. The team used Git for version control and GitHub Actions for continuous integration. Demo accounts and seed data were prepared early so that integration could be tested throughout development.

Table: Resource planning summary

| Resource | Description |
| Backend services | Five FastAPI services |
| Frontend | Next.js application |
| Gateway | NGINX |
| Databases | Five SQLite files |
| Tests | 24 backend and 17 frontend |
| Documentation | Report, paper, deck |

## Implementation of Project

Implementation followed the approved design. The identity service provides JWT authentication and consent artifacts. The records service seals trauma profiles and manages QR tokens. The ABDM service builds FHIR bundles and traces. The NHCX service manages bills and claims. The SOS service delivers alerts and email. The frontend provides patient, hospital, admin, and scanner interfaces. Deployment artifacts support Docker Compose, single-container, and local modes.

## Business Results

The prototype demonstrates technical feasibility and reproducible integration. Automated tests pass, the end-to-end workflow passes, and the benchmark shows sub-millisecond local emergency retrieval. The system can be demonstrated without live national gateway dependencies.

Table: Business results

| Result | Value |
| Service tests | 24 passing |
| End-to-end steps | 18 passing |
| Frontend tests | 17 passing |
| Benchmark requests | 1,000 |
| Median retrieval time | 0.644 ms |
| 95th percentile | 0.743 ms |
| Design threshold | 800 ms |

## Other Results

The project also produced an IJIRT-style research paper, a project report, a presentation deck, a static project site, and deployment documentation. The paper reports 25 verified references and measured evaluation results. The repository includes CI workflows and published container images.

## Conclusion

The ABHA Health Card project met its objectives within the defined scope. It demonstrates secure emergency retrieval, FHIR interoperability, claims synchronization, and emergency notification. Its limitations, including simulated gateways and lack of clinical validation, are clearly stated. The prototype provides a foundation for future work with real ABDM and NHCX integration.

## References

1. Project repository: ABHA Health Card, Group SY1512, MIT-ADT University.
2. IJIRT paper: An ABHA-Integrated Emergency Health Card Prototype.
3. README and deployment documentation.
## Detailed Customer Profile

The customer group includes students, faculty evaluators, and demonstration hospital users. Patients need a simple way to carry emergency facts. Hospitals need quick access to trauma profiles and a path to standardized records. Administrators need audit visibility. The solution addresses these needs through a single web application and public scanner.

## Detailed Challenge Analysis

The challenge has four parts. First, emergency data must be readable without patient authentication. Second, the same data must not be exposed in plaintext. Third, clinical records and claims must be standardized. Fourth, alerts must reach staff and contacts quickly. Each part required a specific technical approach and careful scope control.

## Detailed Solution Architecture

The solution uses five services behind a gateway. The records service protects trauma data. The identity service manages users and consent. The ABDM service converts records to FHIR. The NHCX service manages claims. The SOS service delivers alerts. The frontend unifies these capabilities for three roles.

Table: Feature summary

| Feature | Benefit |
| Emergency QR profile | Fast responder access |
| AES-128-GCM sealing | Confidentiality at rest |
| HMAC-SHA256 | Tamper detection |
| Token rotation | Limits leaked card reuse |
| FHIR bundles | Standardized records |
| Claim state machine | Auditable claims |
| WebSocket alerts | Low-latency notification |
| SMTP fallback | Contact reachability |

## Implementation Timeline

The implementation followed the eleven-week phase plan in the project report. Backend services were built first, followed by frontend and integration. Testing and documentation were continuous. The final week focused on polish, deployment, and report preparation.

## Quality Assurance

Quality assurance included 24 backend tests, 17 frontend tests, and an 18-step end-to-end smoke test. A 1,000-request benchmark verified emergency retrieval. These checks provide confidence in the prototype but do not constitute clinical validation.

## Deployment Story

The system was deployed on Render's free tier. The deployment sleeps after 15 minutes without requests and wakes in a measured 91 seconds. The application address remains valid while asleep, so a scanned card still resolves. This demonstrates a low-cost demo path.

## Lessons Learned

The team learned that clear scope boundaries, service isolation, and automated tests are essential. Simulated gateways allowed progress without external dependencies. Documentation should be updated with code. Security requires governance beyond encryption.

## Future Opportunities

Future opportunities include real ABDM and NHCX integration, offline profile caching, managed key storage, responder identity, and clinical usability studies. These would move the prototype toward production readiness.

## Final Summary

The ABHA Health Card project is a successful academic prototype. It meets its objectives, demonstrates integration, and documents its limitations. It provides a strong foundation for future healthcare interoperability work.
