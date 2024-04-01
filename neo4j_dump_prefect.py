from prefect import flow
from neo4j_summary import neo4j_summary
from bento.common.secret_manager import get_secret
from neo4j_dump import neo4j_dump

NEO4J_URI = "neo4j_uri"
NEO4J_USER = "neo4j_user"
NEO4J_PASSWORD = "neo4j_password"

@flow(name="neo4j secret summary", log_prints=True)
def neo4j_dump_prefect(
        secret_name,
        s3_bucket,
        s3_folder,
        dump_file_name = "test_dump.dump"
        
):
    secret = get_secret(secret_name)
    neo4j_uri = secret[NEO4J_URI]
    neo4j_user = secret[NEO4J_USER]
    neo4j_password = secret[NEO4J_PASSWORD]
    neo4j_dump(dump_file_name, neo4j_uri, neo4j_user, neo4j_password, s3_bucket, s3_folder)

if __name__ == "__main__":
    # create your first deployment
    neo4j_dump_prefect.serve(name="neo4j_deployment")
