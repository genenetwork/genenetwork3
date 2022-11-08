"""
Init data in resource_categories table
"""

from yoyo import step

__depends__ = {'20221108_03_Pbhb1-create-resource-categories-table'}

steps = [
    step(
        """
        INSERT INTO resource_categories VALUES
        ('fad071a3-2fc8-40b8-992b-cdefe7dcac79', 'mrna', 'mRNA Dataset'),
        ('548d684b-d4d1-46fb-a6d3-51a56b7da1b3', 'phenotype', 'Phenotype (Publish) Dataset'),
        ('48056f84-a2a6-41ac-8319-0e1e212cba2a', 'genotype', 'Genotype Dataset')
        """,
        """
        DELETE FROM resource_categories WHERE resource_category_id IN
        (
            'fad071a3-2fc8-40b8-992b-cdefe7dcac79',
            '548d684b-d4d1-46fb-a6d3-51a56b7da1b3',
            '48056f84-a2a6-41ac-8319-0e1e212cba2a'
        )
        """)
]
