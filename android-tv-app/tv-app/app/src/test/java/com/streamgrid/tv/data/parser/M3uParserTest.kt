package com.streamgrid.tv.data.parser

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.StringReader

class M3uParserTest {

    private val sampleM3u = """
        #EXTM3U
        #EXTINF:-1 group-title="1. BD Sports" tvg-id="ch_55" tvg-logo="https://example.com/gtv.png",Gazi TV HD 1
        https://app.ncare.live/gtv1.m3u8
        #EXTINF:-1 group-title="1. BD Sports" tvg-id="ch_55" tvg-logo="https://example.com/gtv.png",Gazi TV HD 2
        https://app24.jagobd.com.bd/gtv2.m3u8
        #EXTINF:-1 group-title="1. BD Sports" tvg-id="TSports.bd" tvg-logo="https://example.com/ts.png",T Sports HD 1
        #EXTVLCOPT:http-user-agent=CustomAgent/1.0
        #EXTVLCOPT:http-referrer=https://tsports.com/
        https://tvsen5.aynaott.com/tsports/index.m3u8#skym3u.dev
        #EXTINF:-1 group-title="5. All Sports" tvg-id="StarSports1.in" tvg-logo="https://example.com/ss1.png",Star Sports 1 HD
        https://example.com/ss1.m3u8
        #EXTINF:-1 group-title="5. All Sports" tvg-id="StarSports2.in" tvg-logo="https://example.com/ss2.png",Star Sports 2 HD
        https://example.com/ss2.m3u8
    """.trimIndent()

    @Test
    fun `groups multi-server channels by tvgId while keeping distinct channels separate`() {
        val channels = M3uParser.parse(StringReader(sampleM3u), groupMultiServer = true)

        assertEquals(4, channels.size)

        val gtv = channels[0]
        assertEquals("Gazi TV HD", gtv.name)
        assertEquals(2, gtv.servers.size)
        assertEquals("https://app.ncare.live/gtv1.m3u8", gtv.servers[0].url)
        assertEquals("https://app24.jagobd.com.bd/gtv2.m3u8", gtv.servers[1].url)

        val tsports = channels[1]
        assertEquals("T Sports HD 1", tsports.name)
        assertEquals("https://tvsen5.aynaott.com/tsports/index.m3u8", tsports.servers[0].url)
        assertEquals("CustomAgent/1.0", tsports.servers[0].userAgent)
        assertEquals("https://tsports.com/", tsports.servers[0].referrer)

        assertEquals("Star Sports 1 HD", channels[2].name)
        assertEquals("Star Sports 2 HD", channels[3].name)
    }

    @Test
    fun `ungrouped mode keeps every stream as its own channel`() {
        val channels = M3uParser.parse(StringReader(sampleM3u), groupMultiServer = false)
        assertEquals(5, channels.size)
        assertTrue(channels.all { it.servers.size == 1 })
    }
}
