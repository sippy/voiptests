[![Pipeline](https://github.com/sippy/voiptests/actions/workflows/main.yml/badge.svg?branch=wip)](https://github.com/sippy/voiptests/actions/workflows/main.yml?query=branch%3Awip++)

# VoIP Integrated Tests Suite

## Description

This is a "meta-repository" to test interoperability of several popular
open-source VoIP components and their ability to handle basic SIP call
scenarios, both individually and working as a simple VoIP switching system.

The basic test setup looks like the following:

![Alt text](https://docs.google.com/drawings/d/1vGkoxKZxv-acAAs5azTOApArSMWqBz9vIN83TXyIZAM/pub?w=960&h=720 "Test Setup")

In the course of the test, first UA, which we call "Alice", initiates number
of distinct SIP sessions to the System Under Test (SSuT), which is configured
to forward those sessions to the second UA ("Bob") and pin the media to the
RTPProxy. Bob either answers or rejects the specific session (depending on
scenario id passed in the user section of the RURI) and both Alice and Bob
verify that the particular scenario has completed in the expected way.

Both Alice and Bob are built on top of the
[Sippy B2BUA](https://github.com/sippy/b2bua) SIP and RTP stacks.

## Systems Under Test

| SSuT (`MM_TYPE`) | Description | Branches tested in CI |
|------------------|-------------|-----------------------|
| `opensips` | [OpenSIPS](https://github.com/OpenSIPS/opensips) proxy with the `rtpproxy` module | master, 4.0, 3.6 ... 3.0 |
| `kamailio` | [Kamailio](https://github.com/kamailio/kamailio) proxy with the `rtpproxy` module | master, 6.1, 6.0, 5.8 ... 5.1 |
| `b2bua` | [Sippy Python B2BUA](https://github.com/sippy/b2bua) | wip, on Python 3.10 ... 3.14 |
| `go-b2bua` | [Sippy Go B2BUA](https://github.com/sippy/go-b2bua) | master |
| `siphon` | [SIPhon](https://github.com/siphon-project/siphon-sip), both as a proxy and as a B2BUA | main |

## Test Modes: Signalling-only and Signalling+Media

Every test case is executed in two flavours side by side, over both IPv4 and
IPv6:

- **signalling-only**: SIP + SDP are exchanged and validated, but no RTP is
  sent. In this mode Bob also randomly answers with a T.38 (`image/udptl`)
  SDP instead of an audio one.
- **signalling+media** (`rtp-enabled`): in addition to the above, Alice and
  Bob run real RTP endpoints (Sippy RTP stack, G.711/G.722) that stream audio
  to each other via the RTPProxy, following the media addresses negotiated
  through the SSuT, including updates done by re-INVITEs.

Alice marks media-enabled sessions by setting the SDP session name (`s=`) to
`SippyRTP`, which is how Bob picks the matching mode. SSuTs that rewrite the
SDP have to preserve the `s=` line (e.g. `sdp_keep_session_name` in SIPhon
B2BUA mode). Test cases that explicitly verify no-media timeouts (`t13`,
`t14`) never generate RTP regardless of mode. Alice can be forced into the
signalling-only mode with `-s`.

## What Gets Verified

- Each scenario completes the expected way on both Alice's and Bob's side
  (ringing, early media, answer, failure code, CANCEL, re-INVITE outcome,
  disconnect etc).

- The SSuT rewrites the SDP correctly in all relevant INVITEs, 183s, 200s and
  ACKs, replacing original random media IP/port with the IP/port of the
  RTPProxy, which signifies proper execution of the RTPProxy Control Protocol
  (RTPPC) between the particular SSuT and the RTPProxy.

- Upon test completion session and command counters are pulled from the
  RTPProxy over a dedicated stats socket and compared against the expected
  values specific to that SSuT and scenario: number of RTPPC
  requests/replies/errors, sessions created/destroyed/timed out, and sessions
  with/without RTP. The latter confirms that media actually flowed through
  the RTPProxy in every signalling+media call and did not in the
  signalling-only ones. No-media timeouts and their delivery back to the SSuT
  (notification socket) are checked as well.

- Exit codes of all participants and RTPProxy internal memory checks (debug
  build).

Tests are run against both the debug and the production builds of the
RTPProxy.

## Test Cases

Test cases live in [test_cases/](test_cases/), each implementing both the
Alice and the Bob side of a scenario:

- `t1`..`t10`: basic call, early media, failures at various stages (501, 502,
  503), both in normal and compact SIP form;
- `t11`..`t14`: half-setup and fully-setup no-media timeouts, a two-minute
  signalling-only call;
- `early_cancel`, `early_cancel_lost100`: early CANCEL, also with the lost
  100 Trying;
- `reinvite`, `reinv_fail`, `reinv_onhold`, `reinv_frombob`, `reinv_adelay`,
  `reinv_brkn1`, `reinv_brkn2`, `reinv_bad_ack`: re-INVITE handling, including
  failures, hold/unhold, re-INVITE from the callee, broken SDP and malformed
  ACK;
- `inv_brkn1`: broken SDP in the 183 Session Progress;
- `nated_contact`: NAT'ed Contact header is preserved on re-INVITE.

The subset executed for each SSuT is selected in [functions](functions)
(`TEST_SET`) based on the features it supports. Test cases that are known to
be flaky can be listed in `TEST_SET_MIGHTFAIL`: they are still run, but their
failures do not fail the whole set.

## Configuration Scenarios

The SSuT configuration is picked from [scenarios/](scenarios/) via
`MM_AUTH` (default `simple`):

- `simple`: plain call forwarding with the media anchored to the RTPProxy
  (OpenSIPS, Kamailio, SIPhon proxy);
- `passtr`, `UAC`, `UAS/auth`, `UAS/auth_db/ha1`,
  `UAS/auth_db/calculate_ha1`: digest authentication pass-through, UAC-side
  and UAS-side authentication, including RFC 8760 algorithms (OpenSIPS);
- `b2bua`: SIPhon running in the B2BUA mode.

## RTPProxy Control Transports

The RTPPC transport between the SSuT and the RTPProxy is selected with
`RTPPC_TYPE`: `unix`, `cunix`, `udp`, `udp6`, `tcp`, `tcp6`, or `rtp.io` for
the RTPProxy embedded into the SSuT itself. Not every SSuT supports every
transport, see the CI matrix in
[.github/workflows/main.yml](.github/workflows/main.yml).

The `rtp.io` mode is not part of this repository's CI matrix; instead, this
suite is run in that mode by the CI pipelines of the
[rtp.io](https://github.com/sippy/rtp.io) project itself and of the
[Sippy Python B2BUA](https://github.com/sippy/b2bua).

## Running

The CI builds a Docker image per SSuT and branch on top of the
`ghcr.io/sippy/rtpproxy` image (see
[.github/docker/Dockerfile.ssut](.github/docker/Dockerfile.ssut)) and then
runs [test_run.sh](test_run.sh) inside it once for each scenario, RTPPC
transport and RTPProxy build. To reproduce locally:

```sh
docker build -f .github/docker/Dockerfile.ssut \
  --build-arg MM_TYPE=opensips --build-arg MM_BRANCH=master \
  -t voiptests-opensips .
docker run --rm --privileged --sysctl net.ipv6.conf.all.disable_ipv6=0 \
  -e MM_TYPE=opensips -e MM_BRANCH=master -e MM_AUTH=simple \
  -e RTPPC_TYPE=udp voiptests-opensips voiptests-run-ssut-tests
```

Main knobs: `MM_TYPE`, `MM_BRANCH`, `MM_REV`, `MM_REPO`, `MM_AUTH`,
`RTPPC_TYPE`, `RTPP_VERSION` (`debug` or `production`), `PYTHON_CMD`,
`MM_INIT_DELAY`, `NH_MEDIA_IPS`, `TEST_SET_MIGHTFAIL`.

## TODO

- Add more SSuTs (e.g. Asterisk, FreeSWITCH)

- Add more scenarios (e.g. SIP over TCP/TLS, packet loss, SRTP)

- You name it :)
