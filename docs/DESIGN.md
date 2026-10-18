# CascadeIQ Design Tokens & UI Spec

## Design Tokens
- Canvas background: `#0B0F17`
- Panel & card background: `#121826`
- Border: `#1F2937`
- Text Primary: `#E5E7EB`
- Text Muted: `#9CA3AF`
- State Healthy: `#34D399` (green)
- State Degraded: `#FBBF24` (amber)
- State Failed: `#F87171` (red)
- State Protected: `#38BDF8` (cyan)
- Accent: `#818CF8` (indigo)
- Delta Good: `#34D399`
- Delta Bad: `#F87171`

## Typography
- Inter for UI
- JetBrains Mono for IDs, numbers, and code
- Scales: 12, 14, 16, 20, 28, 40
- KPI numbers: 28 to 40 with tabular numerals

## Graph Visual Encoding
- Shapes:
  - service: rounded rectangle
  - database: barrel/cylinder
  - cache: diamond
  - queue: hexagon
  - external: dashed rectangle
  - gateway: wide rectangle
- Criticality: node size
- State: fill color + accessible icon (check, minus, cross)
- Mitigation: cyan shield badge
- Edge kind: solid (sync), dashed (async), dotted (config), double line (data)
