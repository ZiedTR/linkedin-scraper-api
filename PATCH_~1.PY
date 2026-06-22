# ══════════════════════════════════════════════════════════════
#  PATCH pour main.py — ajoute les 4 nouveaux routers
#  Cherche cette ligne dans ton main.py :
#
#    from routes import profile, company, jobs, posts, articles, location
#
#  et remplace-la par ce bloc :
# ══════════════════════════════════════════════════════════════

from routes import profile, company, jobs, posts, articles, location
from routes import ai, network, batch, webhooks          # ← AJOUTER

# ──────────────────────────────────────────────────────────────
#  Cherche ensuite cette ligne :
#
#    for router in (profile, company, jobs, posts, articles, location):
#        app.include_router(router.router)
#
#  et remplace-la par :
# ──────────────────────────────────────────────────────────────

for router in (profile, company, jobs, posts, articles, location,
               ai, network, batch, webhooks):             # ← AJOUTER
    app.include_router(router.router)

# ──────────────────────────────────────────────────────────────
#  Mets aussi à jour le /health pour refléter les nouveaux endpoints :
# ──────────────────────────────────────────────────────────────
#    "endpoints": {"total": 75, "get": 58, "post": 17},
#    "features": {
#        ...,
#        "ai_enrichment": True,
#        "batch_processing": True,
#        "webhooks": True,
#        "network_graph": True,
#    },
