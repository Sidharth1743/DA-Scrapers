from __future__ import annotations

from dalit_archive_scrapers.models import AssetRule, CandidateRule, SourceDefinition


DEFAULT_CONTENT_SELECTORS = (
    "article",
    "main",
    "#main-content",
    "#content",
    ".entry-content",
    ".post-content",
    ".td-post-content",
    ".jeg_post_content",
    ".jeg_inner_content",
    ".main-content",
    ".page-content",
    ".field--name-body",
)


SOURCE_DEFINITIONS: tuple[SourceDefinition, ...] = (
    SourceDefinition(
        source_id="epw_search_dalit",
        url="https://www.epw.in/search?epw_input=dalit",
        mode="listing_follow",
        seed_fetch_mode="dynamic",
        detail_fetch_mode="dynamic",
        content_selectors=("#main-content", "main", ".content"),
        candidate_rule=CandidateRule(
            include_url_patterns=(r"/journal/.+\.html$",),
            exclude_url_patterns=(r"/author/", r"/journal/\d{4}/\d+$", r"/search", r"/submission-tracker"),
            exclude_text_patterns=(r"^Vol\.", r"^Special Articles$", r"^About"),
            min_text_length=10,
            max_candidates=10,
        ),
        asset_rule=AssetRule(
            exclude_url_patterns=(r"paywall", r"brochure", r"special appeal"),
            allow_images=False,
            include_og_image=False,
        ),
    ),
    SourceDefinition(
        source_id="behanbox_caste",
        url="https://behanbox.com/category/themes/caste/",
        mode="listing_follow",
        content_selectors=("#content", "main"),
        candidate_rule=CandidateRule(
            include_url_patterns=(r"/\d{4}/\d{2}/\d{2}/",),
            exclude_url_patterns=(r"/author/", r"/category/", r"/tag/"),
            max_candidates=6,
        ),
    ),
    SourceDefinition(
        source_id="global_ambedkarites",
        url="https://globalambedkarites.org/?playlist=8dc28d3&video=fa619a6",
        mode="single_page",
        content_selectors=("body", "main"),
        asset_rule=AssetRule(include_og_image=True),
    ),
    SourceDefinition(
        source_id="columbia_dalit_websites",
        url="https://exhibitions.library.columbia.edu/exhibits/show/ambedkar/dalits",
        mode="single_page",
        content_selectors=("#content", "main"),
        asset_rule=AssetRule(include_og_image=False),
    ),
    SourceDefinition(
        source_id="sansad_constituent_assembly_debates",
        url="https://eparlib.sansad.in/handle/123456789/4",
        mode="listing_follow",
        content_selectors=("main", "body"),
        candidate_rule=CandidateRule(
            include_url_patterns=(r"/handle/123456789/\d+",),
            exclude_url_patterns=(r"/handle/123456789/4$", r"/screenreader", r"/help"),
            max_candidates=10,
        ),
        asset_rule=AssetRule(include_og_image=False),
    ),
    SourceDefinition(
        source_id="ghdi_docpage_4505",
        url="https://ghdi.ghi-dc.org/docpage.cfm?docpage_id=4505",
        mode="single_page",
        content_selectors=("body",),
        asset_rule=AssetRule(
            include_url_patterns=(r"/pdf/",),
            include_og_image=False,
        ),
    ),
    SourceDefinition(
        source_id="brambedkar_constitution",
        url="https://library.brambedkar.in/constitution-of-india/",
        mode="single_page",
        content_selectors=("#main-content", "main"),
        asset_rule=AssetRule(
            include_url_patterns=(r"/pdf/",),
            include_og_image=False,
        ),
    ),
    SourceDefinition(
        source_id="scroll_search_dalits",
        url="https://scroll.in/search?q=Dalits&page=1",
        mode="single_page",
        content_selectors=("body",),
        asset_rule=AssetRule(include_og_image=False),
    ),
    SourceDefinition(
        source_id="dalitstudies_annual_reports",
        url="https://www.dalitstudies.org.in/annual-reports/",
        mode="single_page",
        content_selectors=("main", "body"),
        asset_rule=AssetRule(
            include_url_patterns=(r"annual_report",),
            include_text_patterns=(r"^\d{4}",),
            include_og_image=False,
        ),
    ),
    SourceDefinition(
        source_id="theambedkarianchronicle",
        url="https://theambedkarianchronicle.in/",
        mode="single_page",
        content_selectors=("body",),
    ),
    SourceDefinition(
        source_id="themooknayak_home",
        url="https://en.themooknayak.com/",
        mode="listing_follow",
        content_selectors=("body",),
        candidate_rule=CandidateRule(
            include_url_patterns=(r"/(dalit-news|tribal-news|education|society|india|labourer|discussion-interview|health|women-news)/",),
            exclude_url_patterns=(r"/author/", r"/collection/", r"/tag/", r"/environment$"),
            max_candidates=8,
        ),
    ),
    SourceDefinition(
        source_id="thewire_search",
        url="https://thewire.in/search",
        mode="single_page",
        seed_fetch_mode="dynamic",
        content_selectors=("body",),
        asset_rule=AssetRule(include_og_image=False),
    ),
    SourceDefinition(
        source_id="mea_books_writings_ambedkar",
        url="https://www.mea.gov.in/books-writings-of-ambedkar.htm",
        mode="single_page",
        content_selectors=("body",),
        asset_rule=AssetRule(
            include_url_patterns=(r"/Images/CPV/", r"ambedkar", r"volume", r"Volume"),
            include_text_patterns=(r"ambedkar", r"writings", r"speeches", r"\bvol\.", r"\bvolume\b"),
            exclude_url_patterns=(r"passport", r"helpline", r"treaty", r"glossary"),
            include_og_image=False,
        ),
    ),
    SourceDefinition(
        source_id="cvmc_home",
        url="https://www.cvmc.in/",
        mode="listing_follow",
        content_selectors=("main", "#content", "body"),
        candidate_rule=CandidateRule(
            include_url_patterns=(
                r"https://www\.cvmc\.in/act/?$",
                r"https://www\.cvmc\.in/relief/?$",
                r"https://www\.cvmc\.in/resources/?$",
                r"https://www\.cvmc\.in/india/?$",
                r"https://www\.cvmc\.in/karnataka/?$",
                r"https://www\.cvmc\.in/tamil-nadu/?$",
                r"https://www\.cvmc\.in/states/?$",
                r"https://www\.cvmc\.in/faqs/?$",
                r"https://www\.cvmc\.in/about/?$",
                r"https://www\.cvmc\.in/\d{4}/\d{2}/\d{2}/",
            ),
            exclude_url_patterns=(
                r"/contact/?$",
                r"/supreme-court-judgment/?$",
                r"#",
            ),
            max_candidates=12,
        ),
        asset_rule=AssetRule(
            include_url_patterns=(r"/wp-content/uploads/.+\.(pdf|xlsx?)$", r"/flipbook-df_", r"/dearflip-"),
            include_text_patterns=(r"report", r"judgment", r"act", r"rules", r"contingency", r"relief"),
            allow_images=False,
            include_og_image=False,
            max_documents=12,
        ),
    ),
    SourceDefinition(
        source_id="cvmc_supreme_court_judgment",
        url="https://www.cvmc.in/supreme-court-judgment/",
        mode="single_page",
        content_selectors=("main", "#content", "body"),
        asset_rule=AssetRule(
            include_url_patterns=(r"/wp-content/uploads/Judgment/.+\.pdf$",),
            include_text_patterns=(r"criminal appeal", r"judgment", r"appeal"),
            allow_images=False,
            include_og_image=False,
            max_documents=26,
        ),
    ),
)


DEFINITIONS_BY_URL = {definition.url: definition for definition in SOURCE_DEFINITIONS}
DEFINITIONS_BY_ID = {definition.source_id: definition for definition in SOURCE_DEFINITIONS}
