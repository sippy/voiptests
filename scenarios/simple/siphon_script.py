from siphon import proxy, rtpengine, log

PROFILE = "rtp_passthrough"
ALICE_PORT = 5061
BOB_PORT = 5062


@proxy.on_request
async def route(request):
    log.info(f"SIPhon received a request {request.method} from {request.source_ip}")

    if request.method == "INVITE" and request.has_body("application/sdp"):
        await rtpengine.offer(request, profile=PROFILE)

    if request.method == "BYE":
        await rtpengine.delete(request)

    request.record_route()

    if request.in_dialog:
        request.loose_route()
        request.relay()
        return

    if request.source_port == ALICE_PORT:
        request.ruri.port = BOB_PORT
    else:
        request.ruri.port = ALICE_PORT
    request.relay()


@proxy.on_reply
async def reply_route(request, reply):
    log.info(f"SIPhon received a reply {reply.status_code}/{request.method}")
    if reply.status_code in (180, 183) or 200 <= reply.status_code < 300:
        if reply.has_body("application/sdp"):
            await rtpengine.answer(reply, profile=PROFILE)
    reply.relay()


@proxy.on_failure
async def failure_route(request, reply):
    if request.method == "INVITE" and not request.in_dialog:
        await rtpengine.delete(request)
    reply.relay()


@proxy.on_cancel
async def cancel_route(request):
    await rtpengine.delete(request)
