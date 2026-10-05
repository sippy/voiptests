from siphon import b2bua, rtpengine, log

PROFILE = "rtp_passthrough"
BOB_PORT = 5062


def bob_uri(call):
    user = call.ruri.user
    host = call.source_ip
    if ":" in host:
        host = f"[{host}]"
    return f"sip:{user}@{host}:{BOB_PORT}"


@b2bua.on_invite
async def on_invite(call):
    log.info(f"SIPhon B2BUA received INVITE {call.from_uri} -> {call.ruri}")
    await rtpengine.offer(call, profile=PROFILE)
    call.dial(bob_uri(call))


@b2bua.on_early_media
async def on_early_media(call, reply):
    await rtpengine.answer(reply, profile=PROFILE, call=call)


@b2bua.on_answer
async def on_answer(call, reply):
    await rtpengine.answer(reply, profile=PROFILE, call=call)


@b2bua.on_failure
async def on_failure(call, code, reason):
    await rtpengine.delete(call)
    call.reject(code, reason)


@b2bua.on_bye
async def on_bye(call, initiator):
    await rtpengine.delete(call)


@b2bua.on_cancel
async def on_cancel(call):
    await rtpengine.delete(call)
