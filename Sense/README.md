## 👁️ The Sensory Nervous System (`Sense`)

Brain OS implements the UNIX philosophy via a completely decoupled transducer system called **`Sense`**.

In biology, the brain does not process raw photons; the retina transduces them into action potentials. Similarly, LLMs should not read raw HTML or massive Git trees. `Sense` fetches external stimuli (websites, repos, PDFs), strips the noise, and transduces them into strictly formatted XML "Action Potentials" that ensure zero context bloat.

**Usage Example:**
Because `Sense` is an independent workspace package, it can be piped directly into any terminal or script:
`uv run sense scrape "https://news.ycombinator.com" > output.md`

**Security:**
`Sense` includes strict Shift-Left SSRF (Server-Side Request Forgery) protection. It will actively block attempts to resolve `localhost`, loopback addresses, or private AWS metadata IPs.
