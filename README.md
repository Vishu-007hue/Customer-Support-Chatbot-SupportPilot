# AI-Powered Customer Support Chatbot Platform

Internship-level implementation with enterprise-style design.

## What Is Implemented

- FastAPI backend with REST APIs
- Dialogflow and Rasa provider abstraction (`NLP_PROVIDER=dialogflow|rasa`)
- MongoDB storage for messages, responses, and handover queue
- Confidence-based response routing
- Optional OpenAI fallback when confidence is very low
- Admin authentication (JWT login)
- Protected admin CRUD endpoints for response templates
- Analytics summary endpoint for dashboard cards
- In-memory TTL cache for intent response templates
- Static frontend chat + mini admin login panel
- Render and Netlify deployment config files
- Basic unit tests for auth and cache services
- Request-level rate limiting for public chat/handover APIs
- Request ID and response-time middleware headers
- Postman collection for quick API demo

## Project Structure

- `backend/app/main.py`: API entrypoint and route wiring
- `backend/app/nlp/`: Dialogflow/Rasa providers and factory
- `backend/app/services/chat_service.py`: chatbot flow, thresholds, fallback, cache usage
- `backend/app/services/auth_service.py`: admin login and JWT verification
- `backend/app/services/admin_service.py`: response CRUD logic
- `backend/app/services/analytics_service.py`: intent and usage aggregations
- `backend/app/services/handover_service.py`: handover queue creation
- `backend/seed_responses.py`: seed initial FAQ responses
- `backend/tests/`: unit tests
- `frontend/`: static UI
- `render.yaml`: Render deployment
- `netlify.toml`: Netlify deployment
- `postman_collection.json`: API testing/demo collection

## Backend Setup

1. Go to backend folder:
   - `cd backend`
2. Create virtual environment and install:
   - `pip install -r requirements.txt`
3. Copy env template:
   - `cp .env.example .env`
4. Update required values in `.env`:
   - `MONGO_URI`
   - `NLP_PROVIDER`
   - Dialogflow or Rasa settings
   - `ADMIN_USERNAME`, `ADMIN_PASSWORD`
   - `JWT_SECRET`
   - `OPENAI_API_KEY` (optional)
5. Seed response templates:
   - `python seed_responses.py`
6. Run API:
   - `uvicorn app.main:app --reload --port 8000`

## Frontend Setup

Serve `frontend/` with any static server.

- Default backend URL is `http://localhost:8000`
- Override by setting `window.__API_BASE_URL__` before loading `main.js`

## API Endpoints

- Public:
  - `GET /health`
  - `POST /api/chat`
  - `POST /api/handover`
  - `POST /api/admin/login`
- Admin (Bearer token required):
  - `GET /api/admin/responses`
  - `POST /api/admin/responses`
  - `PUT /api/admin/responses/{record_id}`
  - `DELETE /api/admin/responses/{record_id}`
  - `GET /api/analytics/summary`

## Testing

From `backend/` run:

- `pytest`

Import `postman_collection.json` into Postman for quick API demo.

## Deployment

- Backend (Render):
  - Uses `render.yaml`
  - Set environment variables in Render dashboard
- Frontend (Netlify):
  - Uses `netlify.toml`
  - Publish directory: `frontend`

## Security and Performance Notes

- JWT protection on admin APIs
- Minimal data storage in chat documents
- Caching for repeated intent response lookups
- Lightweight API structure with clear service separation
- Rate limiting on public write endpoints
- Response tracing via `X-Request-Id` and latency via `X-Response-Time-Ms`
