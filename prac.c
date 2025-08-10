#include<stdio.h>
int main(){
  int n;
  do{
    printf("Enter a number:");
    scanf("%d",&n);
    if(n%2!=0){
      break;
    }
    printf("nice you entered an even number!!:%d\n",n);
  }while(1);
  printf("you have entered an odd number.....loop terminated!!:%d",n);
}
