package com.myorg;

import software.constructs.Construct;
import software.amazon.awscdk.Stack;
import software.amazon.awscdk.StackProps;
import software.amazon.awscdk.services.s3.Bucket;
import software.amazon.awscdk.RemovalPolicy;
import software.amazon.awscdk.services.dynamodb.Attribute;
import software.amazon.awscdk.services.dynamodb.AttributeType;
import software.amazon.awscdk.services.dynamodb.Table;
import software.amazon.awscdk.services.lambda.Function;
import software.amazon.awscdk.services.lambda.Runtime;
import software.amazon.awscdk.services.lambda.Code;
import java.util.Map;


// import software.amazon.awscdk.Duration;
// import software.amazon.awscdk.services.sqs.Queue;

public class Proj3ParticipationAppStack extends Stack {
    public Proj3ParticipationAppStack(final Construct scope, final String id) {
        this(scope, id, null);
    }

    public Proj3ParticipationAppStack(final Construct scope, final String id, final StackProps props) {
        super(scope, id, props);

        Bucket bucket = Bucket.Builder.create(this, "Proj3Images")
    .bucketName("proj3-images-nchetty2025") // Replace with something globally unique
    .removalPolicy(RemovalPolicy.DESTROY)
    .autoDeleteObjects(true)
    .build();

    //dynamo table 
    Table table = Table.Builder.create(this, "Proj3ParticipationTable")
            .tableName("proj3-participation-records")
            .partitionKey(Attribute.builder().name("email").type(AttributeType.STRING).build())
            .sortKey(Attribute.builder().name("meeting_date").type(AttributeType.STRING).build())
            .removalPolicy(RemovalPolicy.DESTROY)
            .build();
        //lambda 
        Function lambdaFunction = Function.Builder.create(this, "Proj3Lambda")
    .runtime(Runtime.PYTHON_3_9)
    .handler("lambda_function.lambda_handler")
    .code(Code.fromAsset("assets/lambda"))
    .environment(Map.of(
        "TABLE_NAME", table.getTableName(),
        "S3_BUCKET", bucket.getBucketName()
    ))
    .build();
    // 4. Grant permissions to Lambda
table.grantReadWriteData(lambdaFunction);
bucket.grantReadWrite(lambdaFunction);

        
    }
}
