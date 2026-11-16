package com.streamgrid.tv.data.parser

import com.streamgrid.tv.data.model.Channel
import com.streamgrid.tv.data.model.StreamServer
import java.io.BufferedReader
import java.io.Reader

/**
 * High-speed streaming M3U/M3U8 parser.
 * Parses line-by-line without loading huge playlists into memory and groups
 * multi-server entries sharing the same (category, tvg-id) into a single Channel
 * with ordered backup servers.
 */
object M3uParser {

    private data class RawEntry(
        val name: String,
        val category: String,
        val logoUrl: String?,
        val tvgId: String?,
        val url: String,
        val userAgent: String?,
        val referrer: String?,
    )

    private val attrRegex = Regex("""([\w-]+)\s*=\s*"([^"]*)"""")
    private val trailingServerNumberRegex = Regex("""\s+\d+$""")
    private val bracketTagRegex = Regex("""\s*\[[^\]]*\]$""")

    fun parse(reader: Reader, groupMultiServer: Boolean = true): List<Channel> {
        val buffered = if (reader is BufferedReader) reader else BufferedReader(reader, 16 * 1024)
        val rawEntries = ArrayList<RawEntry>(512)

        var pendingName: String? = null
        var pendingCategory: String? = null
        var pendingLogo: String? = null
        var pendingTvgId: String? = null
        var pendingUserAgent: String? = null
        var pendingReferrer: String? = null

        buffered.forEachLine { rawLine ->
            val line = rawLine.trim()
            if (line.isEmpty()) return@forEachLine

            when {
                line.startsWith("#EXTM3U", ignoreCase = true) -> Unit

                line.startsWith("#EXTINF:", ignoreCase = true) -> {
                    val commaIdx = findDisplayTitleComma(line)
                    val headerPart = if (commaIdx >= 0) line.substring(0, commaIdx) else line
                    val titlePart = if (commaIdx >= 0) line.substring(commaIdx + 1).trim() else ""

                    val attrs = extractAttributes(headerPart)
                    pendingTvgId = attrs["tvg-id"]?.takeIf { it.isNotBlank() }
                    pendingLogo = attrs["tvg-logo"]?.takeIf { it.isNotBlank() }
                    val rawGroup = attrs["group-title"]?.takeIf { it.isNotBlank() }
                    pendingCategory = rawGroup ?: pendingCategory ?: "Uncategorized"
                    pendingName = titlePart.ifBlank {
                        attrs["tvg-name"]?.takeIf { it.isNotBlank() } ?: "Channel"
                    }
                }

                line.startsWith("#EXTGRP:", ignoreCase = true) -> {
                    val grp = line.substringAfter(":").trim()
                    if (grp.isNotEmpty()) pendingCategory = grp
                }

                line.startsWith("#EXTVLCOPT:", ignoreCase = true) -> {
                    val opt = line.substringAfter(":")
                    when {
                        opt.startsWith("http-user-agent=", ignoreCase = true) ->
                            pendingUserAgent = opt.substringAfter("=").trim()
                        opt.startsWith("http-referrer=", ignoreCase = true) ->
                            pendingReferrer = opt.substringAfter("=").trim()
                    }
                }

                line.startsWith("#") -> Unit

                else -> {
                    val url = sanitizeStreamUrl(line)
                    if (url.isNotEmpty() && pendingName != null) {
                        rawEntries.add(
                            RawEntry(
                                name = pendingName!!,
                                category = pendingCategory ?: "Uncategorized",
                                logoUrl = pendingLogo,
                                tvgId = pendingTvgId,
                                url = url,
                                userAgent = pendingUserAgent,
                                referrer = pendingReferrer,
                            ),
                        )
                    }
                    pendingName = null
                    pendingCategory = null
                    pendingLogo = null
                    pendingTvgId = null
                    pendingUserAgent = null
                    pendingReferrer = null
                }
            }
        }

        return buildChannels(rawEntries, groupMultiServer)
    }

    private fun buildChannels(
        entries: List<RawEntry>,
        groupMultiServer: Boolean,
    ): List<Channel> {
        if (entries.isEmpty()) return emptyList()

        if (!groupMultiServer) {
            return entries.mapIndexed { index, entry ->
                val stableId = fnv1aHex("${entry.category}|${entry.name}|${entry.url}")
                Channel(
                    id = stableId,
                    number = index + 1,
                    name = entry.name,
                    category = entry.category,
                    logoUrl = entry.logoUrl,
                    tvgId = entry.tvgId,
                    servers = listOf(
                        StreamServer(
                            label = "Server 1",
                            url = entry.url,
                            userAgent = entry.userAgent,
                            referrer = entry.referrer,
                        ),
                    ),
                    sortOrder = index,
                )
            }
        }

        // Group servers when they share a category AND a meaningful tvg-id (e.g. Gazi TV HD 1/2/3).
        val grouped = LinkedHashMap<String, MutableList<RawEntry>>(entries.size)
        for (entry in entries) {
            val baseName = cleanBaseName(entry.name)
            val groupKey = if (!entry.tvgId.isNullOrBlank()) {
                "${entry.category.lowercase()}|id:${entry.tvgId.lowercase()}"
            } else {
                "${entry.category.lowercase()}|name:${baseName.lowercase()}"
            }
            grouped.getOrPut(groupKey) { mutableListOf() }.add(entry)
        }

        val channels = ArrayList<Channel>(grouped.size)
        var channelNumber = 1
        for ((groupKey, groupItems) in grouped) {
            val first = groupItems.first()
            val displayName = if (groupItems.size > 1) {
                cleanDisplayGroupName(first.name)
            } else {
                first.name
            }
            val logo = groupItems.firstNotNullOfOrNull { it.logoUrl }
            val servers = groupItems.distinctBy { it.url }.mapIndexed { idx, item ->
                val label = extractServerLabel(item.name, idx + 1)
                StreamServer(
                    label = label,
                    url = item.url,
                    userAgent = item.userAgent,
                    referrer = item.referrer,
                )
            }
            val stableId = fnv1aHex(groupKey)
            channels.add(
                Channel(
                    id = stableId,
                    number = channelNumber,
                    name = displayName,
                    category = first.category,
                    logoUrl = logo,
                    tvgId = first.tvgId,
                    servers = servers,
                    sortOrder = channelNumber - 1,
                ),
            )
            channelNumber++
        }
        return channels
    }

    private fun extractAttributes(header: String): Map<String, String> {
        val map = HashMap<String, String>(6)
        for (match in attrRegex.findAll(header)) {
            map[match.groupValues[1].lowercase()] = match.groupValues[2]
        }
        return map
    }

    private fun findDisplayTitleComma(line: String): Int {
        var inQuotes = false
        for (i in line.indices) {
            when (line[i]) {
                '"' -> inQuotes = !inQuotes
                ',' -> if (!inQuotes) return i
            }
        }
        return -1
    }

    private fun cleanBaseName(name: String): String {
        return name
            .replace(bracketTagRegex, "")
            .replace(trailingServerNumberRegex, "")
            .trim()
    }

    private fun cleanDisplayGroupName(name: String): String {
        val cleaned = cleanBaseName(name)
        return cleaned.ifBlank { name }
    }

    private fun extractServerLabel(name: String, index: Int): String {
        val bracketMatch = bracketTagRegex.find(name)
        if (bracketMatch != null) {
            return "Server $index ${bracketMatch.value.trim()}"
        }
        return "Server $index"
    }

    private fun sanitizeStreamUrl(raw: String): String {
        val trimmed = raw.trim()
        // Some playlists append #skym3u.dev or similar tracking tags after the URL
        val hashIndex = trimmed.indexOf('#')
        return if (hashIndex > 0) trimmed.substring(0, hashIndex).trim() else trimmed
    }

    private fun fnv1aHex(input: String): String {
        var hash = -3750763034362895579L
        for (ch in input) {
            hash = hash xor ch.code.toLong()
            hash *= 1099511628211L
        }
        return hash.toULong().toString(16)
    }
}
