# Jenkins Credentials Setup

## 1. GitHub Token
- **Manage Jenkins** → **Credentials** → **Add Credentials**
- Kind: Secret text
- Secret: `ghp_YOUR_GITHUB_TOKEN`
- ID: `github-token`

## 2. GCP Service Account
- Kind: Secret file
- File: `gen-lang-client-0068855436-6ac47f371465.json`
- ID: `gcp-key`

## 3. GROQ API Key
- Kind: Secret text
- Secret: `gsk_YOUR_KEY`
- ID: `GROQ_API_KEY`

## 4. Tavily API Key
- Kind: Secret text
- Secret: `tvly-YOUR_KEY`
- ID: `TAVILY_API_KEY`

## 5. Google API Key
- Kind: Secret text
- Secret: `AIza-YOUR_KEY`
- ID: `GOOGLE_API_KEY`