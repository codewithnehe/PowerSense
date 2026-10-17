
# ⚡ PowerSense

### Predict power outages. Prepare before the lights go out.

PowerSense is an AI-powered electricity outage awareness and preparedness web application designed for Nigeria. It combines community outage reports, weather forecasts, and available national grid data to estimate local power outage risk and provide personalized, actionable reminders using an open-weight AI model.

Built for **Hacktoberfest 2026**, PowerSense aims to help Nigerians prepare for electricity interruptions by knowing when to charge their devices, pump water, protect perishable goods, and plan important work.

> **Our mission:** Help people make better decisions about electricity outages through community-powered data and open-source AI.

**Project status:** In development  
**Hackathon:** Hacktoberfest 2026  
**Primary audience:** Students, small business owners, and remote workers in Nigeria.

---

## 📌 Table of Contents

- [The Problem](#-the-problem)
- [Our Solution](#-our-solution)
- [Key Features](#-key-features)
- [Who Is PowerSense For?](#-who-is-powersense-for)
- [How It Works](#-how-it-works)
- [AI Integration](#-ai-integration)
- [Data Sources](#-data-sources)
- [Power Window](#-the-power-window)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Development Roadmap](#-development-roadmap)
- [Privacy and Security](#-privacy-and-security)
- [Limitations](#-limitations)
- [Contributing](#-contributing)
- [Hacktoberfest 2026](#-hacktoberfest-2026)
- [License](#-license)

## 🚨 The Problem

Electricity interruptions are a recurring challenge for households, students, and businesses across Nigeria.

Unexpected outages can lead to:

- Dead phones, laptops, and other essential devices.
- Interrupted online classes, remote work, and virtual meetings.
- Empty water tanks when electric pumping systems stop working.
- Spoiled food and other temperature-sensitive products.
- Lost productivity due to poor preparation.

Although people often share outage information within their communities, reliable, location-specific information can be difficult to access in one place.

PowerSense addresses this problem by combining available data and community reports to provide a practical picture of current conditions and possible outage risks.

## 💡 Our Solution

PowerSense transforms electricity reports and environmental signals into useful preparedness recommendations.

Instead of simply displaying whether electricity is available, PowerSense helps answer three questions:

1. **What is happening?** Is electricity currently reported to be available or unavailable nearby?
2. **What might happen next?** Is there evidence of increased outage risk over the next few hours?
3. **What should I do?** What practical actions can I take based on my needs?

The application uses deterministic, rule-based logic to assess the available signals. An open-weight AI model then turns the assessment into clear, personalized reminders in plain English or Nigerian Pidgin.

PowerSense communicates uncertainty honestly. It provides risk estimates, not guaranteed predictions.

## ✨ Key Features

### 1. Community-powered outage reporting

Users can report local electricity conditions by selecting:

- **Light is on** — electricity is currently available.
- **Light is off** — electricity is currently unavailable.

Reports include a timestamp and, when location access is granted, geographical coordinates. Nearby reports can help identify local electricity conditions.

### 2. Location-aware outage information

PowerSense uses location information to identify relevant reports and weather conditions around the user.

Location is captured when the user submits a report rather than relying exclusively on an old signup location.

### 3. Weather-based risk assessment

Weather forecasts can identify conditions such as heavy rain and storms that may be associated with increased outage risk.

Weather is treated as a risk signal, not proof that an outage will occur.

### 4. AI-generated preparedness reminders

An open-weight AI model generates concise, context-aware recommendations based on the assessed risk, time of day, location context, and optional user routines.

Examples:

- "Light's confirmed out nearby. Charge your phone and laptop when electricity returns."
- "Heavy rain is forecast in your area. If you have electricity now, consider charging your devices and pumping water."
- "You have an online meeting soon. Check your battery level and keep your mobile data ready."

These are illustrative examples, not live predictions.

### 5. Power Window dashboard

A central dashboard brings together current reported conditions, estimated risk, supporting evidence, and recommended actions.

### 6. Offline-first reporting

The planned offline-first workflow stores submitted reports locally with timestamps and available coordinates when a network connection is unavailable, then synchronizes them when connectivity returns.

GPS may work offline if the device can obtain a location fix, but submitting and synchronizing reports requires the appropriate application capabilities and connectivity.

### 7. Alert feedback

Users can indicate whether an alert was useful or accurate.

Feedback can support future evaluation of alert quality without assuming that the model is already improving its predictions.

### 8. Modular integrations

Data providers, outage assessment rules, and AI model integrations are kept separate so contributors can replace or extend individual components without redesigning the entire application.

## 👥 Who Is PowerSense For?

| User | Challenge | How PowerSense Helps |
|---|---|---|
| Students | Keeping laptops and phones ready for classes and examinations | Encourages charging and preparation before a potential interruption |
| Small business owners | Protecting refrigerated stock and maintaining operations | Provides risk information to support operational planning |
| Remote workers | Staying connected for meetings and deadlines | Suggests device charging, power bank preparation, and connectivity alternatives |

## ⚙️ How It Works

PowerSense follows a simple process:

1. **Collect data:** Retrieve available community outage reports, weather forecasts, and national grid information where a reliable endpoint is available.
2. **Collect local reports:** Allow users to report whether electricity is currently available.
3. **Evaluate signals:** Apply transparent rules to determine the current status and estimated risk.
4. **Generate recommendations:** Provide the assessment and relevant context to an open-weight AI model.
5. **Display the Power Window:** Show the status, evidence, risk level, and suggested actions.
6. **Collect feedback:** Let users report whether the alert was correct or useful.

### Outage states

| State | Confidence | Meaning |
|---|---|---|
| 🔴 Out Now | High, when supported by sufficient local confirmations | Multiple recent reports indicate that electricity is unavailable nearby |
| 🟠 Elevated Risk | Medium | Weather conditions or other relevant signals suggest increased outage risk |
| 🟡 Possible Soon | Low | A significant national grid decline may indicate a broader risk |
| 🟢 All Clear | No elevated risk detected | No configured warning condition has been triggered |

**Important:** "All Clear" does not mean an outage is impossible. It means the available signals have not triggered a warning.

The initial rule for declaring a local outage is at least three qualifying reports. This threshold will need testing and refinement based on report freshness, distance, and reliability.

The planned monitoring cycle is approximately every 10–15 minutes. Actual refresh frequency will depend on provider limits, caching, and deployment configuration.

## 🤖 AI Integration

PowerSense is designed around open-weight AI, aligning with the Hacktoberfest challenge's focus on open-source AI and open-weight models.

### Why use AI?

Traditional rules determine the application's status. AI makes the result easier to understand and turns it into practical guidance for different users.

For example, a high-risk assessment could produce different recommendations for a student, a shop owner, or someone working remotely.

### Proposed models and hosting

| Component | Proposed option | Purpose |
|---|---|---|
| Primary language model | Qwen through Groq-hosted inference | Fast, personalized reminders |
| Alternative model | Gemma | An alternative for generating explanations and recommendations |
| Optional reasoning model | DeepSeek R1 | Exploring explanations of why an alert was triggered |

The final model and provider will be selected after checking current model availability, licensing, inference limits, cost, and the hackathon rules.

A hosted inference API means the application does not need its own GPU server. The selected model must meet the challenge's open-weight requirements; the hosting provider itself is a separate consideration.

### AI input

The model may receive:

- The current rule-based outage state.
- The estimated risk and the signals supporting it.
- Relevant local report summaries.
- The time of day.
- The user's selected profile or routine, if provided.
- The preferred response language.

### AI output

The model generates two or three short, actionable recommendations in plain English or Nigerian Pidgin.

**Design principle:** AI communicates the assessment; it does not invent outage reports, override the rule engine, or present uncertain predictions as facts.

## 🌦️ Data Sources

PowerSense is designed to combine multiple data sources.

| Source | Information | Intended use |
|---|---|---|
| NEPAWatch API | Community-reported outages, confirmation counts, and timestamps, subject to the available API fields | Current local outage awareness |
| OpenWeatherMap | Current weather and forecasts by geographical coordinates | Weather-related risk assessment |
| PowerSense reports | User-submitted electricity status, timestamp, and available location | Local condition reporting |
| Nigeria national grid data | Generation levels and grid health, if a reliable endpoint is available | Optional grid-wide early warning |

Provider access, response formats, rate limits, and current endpoint availability must be verified during implementation. PowerSense should remain functional without national grid data.

The application should cache external responses, respect provider terms, and avoid making a separate external API request for every user interaction.

## 🪟 The Power Window

The Power Window is the main dashboard of PowerSense.

It contains three essential sections:

### Current status

Displays the detected state, when the latest relevant report was received, and the evidence supporting the assessment.

### Estimated risk

Shows a low, medium, or high risk estimate for the next few hours, with a short explanation of the contributing signals.

### Suggested actions

Presents personalized recommendations, such as:

- Charge essential devices.
- Pump water if electricity is available and water storage is needed.
- Prepare a power bank or alternative internet connection.
- Protect refrigerated stock when an interruption is reported or considered likely.
- Complete time-sensitive work while the necessary resources are available.

The dashboard is designed to support decisions under uncertainty rather than promise exact outage times.

## 🏗️ System Architecture

The proposed architecture separates data collection, assessment, and AI-generated messaging.

```text
                 ┌─────────────────────────┐
                 │     PowerSense Web App   │
                 │  Power Window & Reports  │
                 └────────────┬────────────┘
                              │
                 ┌────────────▼────────────┐
                 │       Backend API        │
                 │ Reports, status, alerts  │
                 └────────────┬────────────┘
                              │
              ┌───────────────┼────────────────┐
              │               │                │
    ┌─────────▼──────┐ ┌──────▼───────┐ ┌──────▼────────┐
    │ Local Reports  │ │ Weather Data │ │ NEPAWatch API │
    │ PowerSense DB  │ │ OpenWeather  │ │ Community Data│
    └─────────┬──────┘ └──────┬───────┘ └──────┬────────┘
              │               │                │
              └───────────────┼────────────────┘
                              │
                 ┌────────────▼────────────┐
                 │   Rule-Based Assessment │
                 │ Status, evidence, risk  │
                 └────────────┬────────────┘
                              │
                 ┌────────────▼────────────┐
                 │   Open-Weight AI Model   │
                 │ Personalized reminders   │
                 └────────────┬────────────┘
                              │
                 ┌────────────▼────────────┐
                 │       Power Window       │
                 │ Alerts & suggested steps │
                 └─────────────────────────┘
```

This diagram represents the intended architecture, not a claim that every component has already been implemented.

### Architectural principles

- Keep data-source integrations independent.
- Keep outage assessment rules separate from language generation.
- Cache external data and respect free-tier request limits.
- Store user reports with timestamps and appropriate validation.
- Support offline report queuing and later synchronization.
- Make it possible to replace the AI model or provider.
- Provide useful fallback behavior when an external service is unavailable.

## 🧰 Technology Stack

The following technologies are proposed for the project. The final stack may change as implementation progresses.

| Layer | Technology or service | Purpose |
|---|---|---|
| Frontend | Lightweight web application | Dashboard, reporting, and alert presentation |
| Backend | Small REST API | Report ingestion, risk assessment, and data integration |
| Database | Lightweight persistent database | Store reports, timestamps, and alert feedback |
| Weather | OpenWeatherMap API | Weather forecasts and current conditions |
| Outage reports | NEPAWatch API | Community outage information |
| AI inference | Groq-hosted Qwen or another compliant open-weight model | Personalized reminders |
| Offline support | Browser storage and synchronization logic | Queue reports while offline |
| Deployment | A suitable web host and backend runtime | Publish the application |

The initial version does not require a complex microservices architecture, a GPU server, or a Kubernetes cluster. A small, modular application is sufficient for validating the idea.

## 🚀 Getting Started

PowerSense is under development. The following setup describes the intended workflow; actual commands and filenames may change to match the repository implementation.

### Prerequisites

- Git
- Node.js and npm, if the application uses a Node.js-based frontend or backend
- API credentials for the selected weather and AI providers
- A browser that supports the required location features

### 1. Clone the repository

Replace the placeholder with the actual repository URL.

```bash
git clone <YOUR_REPOSITORY_URL>
cd PowerSense
```

### 2. Install dependencies

Run the appropriate installation command in the frontend and backend directories once the project structure has been established.

```bash
npm install
```

### 3. Configure environment variables

Create the appropriate environment file based on the project's configuration.

```env
WEATHER_API_KEY=your_weather_api_key
AI_API_KEY=your_ai_provider_api_key
AI_MODEL=your_selected_open_weight_model
DATABASE_URL=your_database_connection_string
```

These names are illustrative. Use the exact variables required by the implemented application.

### 4. Start the application

Run the project's configured development command after dependencies and environment variables have been set up.

```bash
npm run dev
```

If the frontend and backend are separate applications, start each service using its own documented command.

### 5. Test the reporting workflow

Once the relevant features are available:

1. Open the application in a browser.
2. Grant location access if you want to submit a location-aware report.
3. Select **Light is on** or **Light is off**.
4. Check that the report is recorded with the correct timestamp and location information.
5. Open the Power Window and inspect the current status and recommendations.

**Location note:** Browser geolocation generally requires HTTPS or localhost. Location access may be unavailable or denied on some devices.

## 🔐 Environment Variables

Keep secrets in environment variables rather than committing them to Git.

| Variable | Description |
|---|---|
| `WEATHER_API_KEY` | Credential for the weather provider |
| `AI_API_KEY` | Secret key for the selected hosted inference provider |
| `AI_MODEL` | Configured model identifier |
| `DATABASE_URL` | Database connection string, if required |
| `NEPAWATCH_API_URL` | Configured outage-data endpoint, if required |

These variables are a proposed configuration reference and should be adjusted to match the actual implementation.

Never expose secret API keys in frontend code, public repositories, screenshots, or client-side environment variables. AI inference requests that require a secret should be handled by the backend.

## 🗺️ Development Roadmap

PowerSense will be built incrementally, prioritizing a working reporting and alert workflow before adding more advanced integrations.

- [ ] **Phase 1: Community reporting**
  - [ ] Create the electricity reporting page.
  - [ ] Implement "Light is on" and "Light is off" actions.
  - [ ] Capture available location coordinates and timestamps.
  - [ ] Persist reports in a database.

- [ ] **Phase 2: Offline support**
  - [ ] Queue reports locally when connectivity is unavailable.
  - [ ] Synchronize queued reports when the connection returns.
  - [ ] Prevent duplicate submissions during synchronization.

- [ ] **Phase 3: Outage data integration**
  - [ ] Integrate the NEPAWatch API.
  - [ ] Display relevant reports for the user's area.
  - [ ] Implement caching and API rate-limit handling.

- [ ] **Phase 4: Weather integration**
  - [ ] Retrieve weather forecasts for the relevant coordinates.
  - [ ] Identify configured storm and heavy-rain signals.
  - [ ] Provide fallback behavior when weather data is unavailable.

- [ ] **Phase 5: Rule-based assessment**
  - [ ] Implement the four outage states.
  - [ ] Introduce report freshness, proximity, and confirmation thresholds.
  - [ ] Display the evidence supporting each assessment.

- [ ] **Phase 6: Open-weight AI integration**
  - [ ] Select a compliant model and inference provider.
  - [ ] Generate concise personalized recommendations.
  - [ ] Support plain English and Nigerian Pidgin.
  - [ ] Add safe fallback messages if inference fails.

- [ ] **Phase 7: Power Window dashboard**
  - [ ] Display current status and estimated risk.
  - [ ] Show the latest relevant reports.
  - [ ] Present personalized actions.
  - [ ] Collect alert feedback.

- [ ] **Phase 8: Demo and evaluation**
  - [ ] Prepare clearly labelled sample reports.
  - [ ] Test the application on mobile devices.
  - [ ] Evaluate false reports and alert accuracy.
  - [ ] Publish the project write-up for Hacktoberfest.

- [ ] **Bonus: National grid integration**
  - [ ] Investigate reliable, accessible grid-data endpoints.
  - [ ] Add a grid-wide warning signal if a suitable source is available.

## 🔒 Privacy and Security

PowerSense handles location-related information, so privacy is a core design consideration.

The project aims to:

- Request location access only when needed.
- Explain why location information is useful.
- Avoid requiring an account for the initial demonstration.
- Validate incoming reports on the backend.
- Apply sensible rate limits to prevent report spam.
- Avoid storing unnecessary personal information.
- Protect API credentials and database access.
- Define appropriate retention and deletion policies for stored reports.
- Avoid publishing precise user locations unnecessarily.

Offline storage should be designed carefully because reports stored on a device may remain accessible to someone using that device.

## ⚠️ Limitations

PowerSense is a preparedness tool, not an official electricity utility or guaranteed outage-prediction service.

- **Community data can be incomplete:** Reports may be missing, delayed, inaccurate, or submitted from different parts of a neighborhood.
- **Weather is indirect evidence:** A storm can increase risk without causing an outage.
- **National grid information is not neighborhood-specific:** A generation decline does not prove that a particular street will lose electricity.
- **AI can make mistakes:** Model-generated recommendations must be grounded in the assessment and validated input.
- **Internet access is still needed for synchronization:** Offline reports cannot be shared with the server until connectivity returns.
- **Coverage depends on data availability:** Areas with few reports may receive less reliable assessments.

PowerSense will communicate these limitations rather than presenting estimates as certain outcomes.

## 🤝 Contributing

Contributions are welcome! PowerSense is intended to be an open, collaborative project, and contributors can help improve the application, its data integrations, and its user experience.

### Areas where you can contribute

- Frontend development and responsive UI/UX.
- Backend APIs and database design.
- Open-weight AI integration and prompt evaluation.
- Outage risk rules and testing.
- Offline-first data synchronization.
- Weather and electricity-data integrations.
- Accessibility and Nigerian Pidgin support.
- Documentation, bug reports, and automated tests.

### Contribution workflow

1. Fork the repository.
2. Create a feature branch.

   ```bash
   git checkout -b feat/your-feature
   ```

3. Make your changes and add relevant tests.
4. Run the available checks.
5. Commit your changes.

   ```bash
   git add .
   git commit -m "feat: describe your change"
   ```

6. Push your branch.

   ```bash
   git push origin feat/your-feature
   ```

7. Open a pull request with a clear explanation of the problem, your changes, and how you tested them.

Please check existing issues and project instructions before starting substantial work. Do not commit secrets, real user location data, or unverified outage claims.

## 🎃 Hacktoberfest 2026

PowerSense is being developed as a Hacktoberfest 2026 project focused on practical applications of open-weight AI.

The project brings together:

- A real-world Nigerian electricity challenge.
- Community-powered local reporting.
- Transparent, rule-based risk assessment.
- Open-weight AI for personalized communication.
- Offline-first thinking for inconsistent connectivity.
- A modular architecture that contributors can extend.

The goal is not simply to generate AI text. It is to use AI as one component of a useful system that helps people make better decisions.

Contributors should verify the current Hacktoberfest participation requirements and the relevant challenge rules before submitting contributions.

## 📄 License

A license has not yet been specified for this project.

Before accepting external contributions or publishing a release, choose an appropriate open-source license and add the corresponding `LICENSE` file. Contributors should be able to understand how the code may be used, modified, and redistributed.

## 🌍 Vision

PowerSense aims to make electricity interruptions less disruptive by helping people prepare with the information available to them.

From a student charging a laptop before class to a shop owner protecting refrigerated goods, the idea is simple:

**Know the situation. Understand the risk. Prepare before the lights go out.**

*PowerSense — Smarter preparation for an unpredictable power supply.*
>>>>>>> 48bd6e40fc54452efcb10e65b844512fa51c84c9
