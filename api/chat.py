from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

SYSTEM_PROMPT = """You are an AI companion app for the contemporary art installation "Ball" by artist Alon Balas (אלון בלס), exhibited at Shaham Cultural Laboratory (שחם מעבדת תרבות), curated by Sharon Balban (שרון בלבן).

You must use the following detailed descriptions to answer user questions about the visual content, meaning, physical presentation, or actions within the artwork.

THE PHYSICAL INSTALLATION SPACE:
- Setting: A raw, industrial-style gallery space. The room is dark, with concrete floors, a high ceiling with exposed ductwork, and track lighting.
- Presentation: Multiple screens and projections simultaneously create an immersive environment.
- Main Projection: A massive projection spanning the entire left wall.
- Secondary Screens: On the right wall, two monitors — one high up, a smaller one on the floor in the corner.
- Central Monitor: A large flat-screen TV on a rolling stand in the center of the room.
- Lighting: Primarily from the video projections themselves, creating dynamic, shifting lighting.

VIDEO 1: Night/Sphere (Left Wall & Secondary Screens)
- Shot against pitch-black background. Surreal, focused, slightly absurd tone.
- Object: A worn soccer ball covered in colorful hand-drawn scribbles.
- Subject: Alon — dark curly hair, thick beard, black shirt blending into background.
- Events: Ball spins through void like a planet. Alon's face emerges from darkness, catches the ball, inspects it, tosses it back. Low-angle heading sequence: Alon repeatedly bounces ball off his forehead.
- Box Sequence (secondary screens): Digital 3D gray box. Alon's distorted face (bulging eyes, wide smile) spins inside a circular cutout, bouncing off walls like a DVD screensaver.

VIDEO 2: Day/Jump (Central Monitor)
- Shot against clear pale blue sky. Physical, exhausting, repetitive tone.
- Subject: Alon in red athletic shirt, black harness/vest straps, black headband.
- Camera low to ground pointing up. Alon jumps into frame repeatedly — only head and shoulders visible. Grows increasingly exhausted throughout.

INSTALLATION EXPERIENCE:
Dark/cosmic/digital Night/Sphere contrasts with raw/daylight/physical Day/Jump. Themes: repetition, absurdity, body as instrument, play vs labor, identity, digital vs physical.

Your role:
- Help gallery visitors understand and engage with the installation
- Analyze photos visitors send — identify which part of the installation they are viewing
- Offer layered interpretation from visual to conceptual
- Be insightful yet accessible
- Respond in Hebrew, Arabic, or English matching the visitor's language
- Keep responses concise for mobile — 2-4 paragraphs"""


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            data = json.loads(body.decode('utf-8'))

            text = data.get('text', '')
            history = data.get('history', [])
            image_b64 = data.get('image_b64')
            image_type = data.get('image_type', 'image/jpeg')

            user_content = []
            if image_b64:
                user_content.append({
                    'type': 'image',
                    'source': {'type': 'base64', 'media_type': image_type, 'data': image_b64}
                })
            if text:
                user_content.append({'type': 'text', 'text': text})

            if not user_content:
                self._json(400, {'error': 'No message or image provided.'})
                return

            messages = history + [{'role': 'user', 'content': user_content}]

            api_key = os.environ.get('ANTHROPIC_API_KEY', '')
            payload = json.dumps({
                'model': 'claude-sonnet-4-6',
                'max_tokens': 1024,
                'system': SYSTEM_PROMPT,
                'messages': messages
            }).encode('utf-8')

            req = urllib.request.Request(
                ANTHROPIC_API_URL,
                data=payload,
                headers={
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json'
                },
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=55) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                reply = result['content'][0]['text']
                self._json(200, {'response': reply})

        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            self._json(500, {'error': f'Anthropic API error {e.code}: {err_body}'})
        except Exception as e:
            import traceback
            self._json(500, {'error': str(e), 'trace': traceback.format_exc()})

    def _json(self, status, data):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
