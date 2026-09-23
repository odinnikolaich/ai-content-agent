# Configuration

Precedence, highest first:

1. CLI arguments
2. Environment variables
3. config/default.yaml
4. application defaults

Secrets are supplied through environment variables or an external secret mechanism; never commit credentials.

Configuration must include target video constraints as configurable values, including duration range, width, height, FPS, language and output format.
