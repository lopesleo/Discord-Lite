# Privacy Policy for Discord Lite

**Last Updated: January 24, 2026**

## Introduction

This Privacy Policy describes how Discord Lite ("we", "our", or "the Plugin") handles your information. We are committed to protecting your privacy and being transparent about our data practices.

## Information We Collect

### Information We DO NOT Collect

Discord Lite does NOT collect, store, or transmit:
- Personal identification information
- Discord user credentials (username, password, email)
- Voice chat content or recordings
- Message history or content
- User behavioral data
- Analytics or usage statistics
- IP addresses
- Device identifiers beyond what's necessary for local operation

### Information Used Locally

The Plugin accesses the following information locally on your Steam Deck for functionality purposes only:
- **Discord Voice Settings**: To display and modify volume levels, input/output devices
- **Voice Channel Information**: To show which channel you're connected to and its participants
- **User Voice States**: To display participant lists and manage per-user volume
- **Game Activity**: To sync your currently playing game with Discord Rich Presence

**Important**: All this information remains on your device and is only used to communicate with your local Discord client via Discord's RPC (Rich Presence Connection).

## How We Use Information

The Plugin uses the locally accessed information solely to:
1. Display your current voice channel and participants
2. Allow you to control volume settings
3. Enable channel switching from the Steam Deck interface
4. Sync your gaming activity with Discord
5. Manage voice settings through the Quick Access Menu

## Data Storage

- **OAuth2 Tokens**: Authentication tokens are stored locally in Decky Loader's plugin data directory on your Steam Deck
- **Settings**: User preferences (language, UI settings) are stored locally
- **No Cloud Storage**: We do not operate any servers or cloud storage systems
- **No External Transmission**: Your data is never transmitted to our servers (we don't have any!)

## Third-Party Services

### Discord

The Plugin communicates exclusively with Discord's services:
- **Discord RPC/API**: All voice and presence data is sent directly to Discord's official endpoints
- **OAuth2 Authentication**: Uses Discord's OAuth2 system for secure authorization
- **Discord's Privacy Policy**: Your interactions with Discord are subject to Discord's Privacy Policy (https://discord.com/privacy)

We do not have access to or control over Discord's data practices.

### Decky Loader

The Plugin runs within the Decky Loader framework on Steam Deck. Decky Loader's data handling is subject to their own policies.

## Data Security

We implement security best practices:
- OAuth2 PKCE (Proof Key for Code Exchange) for authentication without exposing client secrets
- Local-only data storage
- No transmission of sensitive data to external servers
- Open-source code available for security auditing

## Your Rights and Choices

You have the right to:
- **Revoke Access**: Disconnect the Plugin from your Discord account at any time via Discord Settings → Authorized Apps
- **Delete Data**: Uninstall the Plugin to remove all locally stored data
- **Access Source Code**: Review our open-source code at https://github.com/lopesleo/Discord-Lite
- **Opt-Out**: Simply uninstall the Plugin to stop all data access

## Children's Privacy

The Plugin does not knowingly collect information from users under 13 years of age. Discord's Terms of Service require users to be at least 13 years old.

## Changes to This Privacy Policy

We may update this Privacy Policy from time to time. Changes will be posted in the GitHub repository with an updated "Last Updated" date. Continued use of the Plugin after changes constitutes acceptance of the updated policy.

## Open Source Transparency

Discord Lite is open-source software. You can review our complete source code to verify our privacy practices:
- Frontend: `src/index.tsx`
- Backend: `main.py`
- Repository: https://github.com/lopesleo/Discord-Lite

## Data Retention

Since we don't collect or store data on external servers:
- Authentication tokens persist until you revoke access or uninstall the Plugin
- Local settings persist until you uninstall the Plugin
- No data retention policies are necessary as no data is retained externally

## Contact Us

If you have questions about this Privacy Policy or our privacy practices:
- Open an issue on GitHub: https://github.com/lopesleo/Discord-Lite/issues
- Review our source code for transparency

## Compliance

This Plugin operates as a local client-side application and does not fall under typical data processing regulations (GDPR, CCPA) as we do not collect, process, or store user data on external servers. However, we are committed to transparency and user privacy.

---

By using Discord Lite, you acknowledge that you have read and understood this Privacy Policy.
