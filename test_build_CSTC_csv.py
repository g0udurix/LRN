def test_parse_legis_block_from_html(self):
        # Using the TEST_HTML fixture which is already set up
        html_content = build_CSTC_csv.TEST_HTML
        block = build_CSTC_csv.parse_legis_block_from_html(html_content)
        self.assertIsNotNone(block)
        self.assertEqual(block.get('id'), 'mainContent-document')

    def test_iterate_ids_from_html_block(self):
        # Using the TEST_HTML fixture
        html_content = build_CSTC_csv.TEST_HTML
        doc = build_CSTC_csv.LH.fromstring(html_content)
        container = doc.xpath('//div[@id="mainContent-document"]')[0]
        ids_data = list(build_CSTC_csv.iterate_ids_from_html_block(container))

        self.assertEqual(len(ids_data), 6)
        # Check a few key items for correctness
        self.assertIn(('se:29-ss:1-p1:3-p2:a', 'Utilisations prohibées — exemple a) R.R.Q., 1981, c. S-2.1, r. 4, a. 29', ''), ids_data)
        self.assertIn(('ga:l_ii-gb:l_2_11-h1', '§ 2.11 — Électricité', ''), ids_data)
        self.assertIn(('sc-nb:5_3', 'ANNEXE 5.3', ''), ids_data)